/*
 * Pico 2 + TMC2209 + NEMA17 clean tracking firmware.
 *
 * Backend protocol:
 *   PING        -> OK,PONG
 *   STAT        -> E-Stop/driver/trigger-arm snapshot
 *   DRV,1       -> enable drivers
 *   DRV,0       -> disable drivers and stop
 *   ARM,0/1     -> disarm/arm trigger after preflight
 *   SPD,x,y     -> target speed, -1000..1000 per axis
 *   STP         -> stop motion
 *   LZR,1       -> pull trigger servo
 *   LZR,0       -> release trigger servo
 *   TMC_STATUS  -> one-shot driver status
 *
 * Design rule: no periodic serial prints. The backend usually writes only;
 * unsolicited output can fill USB CDC buffers and delay motion/fire commands.
 */

#include <Arduino.h>
#include <Servo.h>
#include <TMCStepper.h>

// Pins: unchanged from the existing hardware.
static constexpr uint8_t X_DIR_PIN = 0;
static constexpr uint8_t X_STEP_PIN = 1;
static constexpr uint8_t X_EN_PIN = 6;
static constexpr uint8_t X_UART_TX = 4;
static constexpr uint8_t X_UART_RX = 5;

static constexpr uint8_t Y_DIR_PIN = 8;
static constexpr uint8_t Y_STEP_PIN = 9;
static constexpr uint8_t Y_EN_PIN = 14;
static constexpr uint8_t Y_UART_TX = 12;
static constexpr uint8_t Y_UART_RX = 13;

static constexpr uint8_t SERVO_PIN = 15;
static constexpr uint8_t ESTOP_PIN = 18;  // LOW = stop

// Trigger calibration from the working system.
static constexpr int SERVO_RELEASE_DEG_DEFAULT = 0;
static constexpr int SERVO_FIRE_DEG_DEFAULT = 175;
int servoReleaseDeg = SERVO_RELEASE_DEG_DEFAULT;
int servoFireDeg = SERVO_FIRE_DEG_DEFAULT;

// TMC2209.
static constexpr float R_SENSE = 0.11f;
static constexpr uint8_t DRIVER_ADDRESS = 0;
static constexpr uint16_t X_RUN_CURRENT_MA = 1200;
static constexpr uint16_t Y_RUN_CURRENT_MA = 1000;
static constexpr uint16_t X_HOLD_CURRENT_MA = 350;
static constexpr uint16_t Y_HOLD_CURRENT_MA = 300;
static constexpr uint16_t MICROSTEPS = 8;

// Speed profile. Backend sends -1000..1000; firmware maps to step/s.
static constexpr float X_MAX_STEPS_PER_SEC = 6000.0f;   // 30:1 gear, ~45 deg/s output
static constexpr float Y_MAX_STEPS_PER_SEC = 4000.0f;   // 20:1 gear, ~45 deg/s output
static constexpr float X_ACCEL_STEPS_PER_SEC2 = 30000.0f;
static constexpr float Y_ACCEL_STEPS_PER_SEC2 = 22000.0f;
static constexpr uint32_t WATCHDOG_TIMEOUT_US = 700000;
static constexpr uint32_t TRIGGER_PULSE_TIMEOUT_US = 1000000;
static constexpr uint16_t STEP_PULSE_US = 2;

HardwareSerial &UART_X = Serial2;
HardwareSerial &UART_Y = Serial1;
TMC2209Stepper driverX(&UART_X, R_SENSE, DRIVER_ADDRESS);
TMC2209Stepper driverY(&UART_Y, R_SENSE, DRIVER_ADDRESS);
Servo triggerServo;

struct AxisState {
  uint8_t stepPin;
  uint8_t dirPin;
  bool invertDir;
  float maxSps;
  float accelSps2;
  volatile float targetSps;
  float currentSps;
  float phase;
};

AxisState axisX{X_STEP_PIN, X_DIR_PIN, false, X_MAX_STEPS_PER_SEC, X_ACCEL_STEPS_PER_SEC2, 0.0f, 0.0f, 0.0f};
AxisState axisY{Y_STEP_PIN, Y_DIR_PIN, false, Y_MAX_STEPS_PER_SEC, Y_ACCEL_STEPS_PER_SEC2, 0.0f, 0.0f, 0.0f};

bool driverEnabled = false;
bool triggerArmed = false;
bool triggerActive = false;
uint32_t triggerActivatedUs = 0;
uint32_t lastCommandUs = 0;
uint32_t lastMotorUpdateUs = 0;
char commandBuffer[80];
uint8_t commandLength = 0;

static void stopMotion() {
  axisX.targetSps = 0.0f;
  axisY.targetSps = 0.0f;
  axisX.currentSps = 0.0f;
  axisY.currentSps = 0.0f;
  axisX.phase = 0.0f;
  axisY.phase = 0.0f;
  digitalWrite(X_STEP_PIN, LOW);
  digitalWrite(Y_STEP_PIN, LOW);
}

static void releaseTrigger() {
  triggerServo.write(servoReleaseDeg);
  triggerActive = false;
  triggerActivatedUs = 0;
}

static void setDrivers(bool enabled) {
  driverEnabled = enabled;
  digitalWrite(X_EN_PIN, enabled ? LOW : HIGH);
  digitalWrite(Y_EN_PIN, enabled ? LOW : HIGH);
  if (!enabled) {
    stopMotion();
  }
}

static float approach(float current, float target, float delta) {
  if (current < target) {
    current += delta;
    return current > target ? target : current;
  }
  if (current > target) {
    current -= delta;
    return current < target ? target : current;
  }
  return current;
}

static void updateAxis(AxisState &axis, float dt) {
  axis.currentSps = approach(axis.currentSps, axis.targetSps, axis.accelSps2 * dt);
  const float speed = axis.currentSps;
  if (speed == 0.0f) {
    axis.phase = 0.0f;
    return;
  }

  const bool direction = (speed > 0.0f) ^ axis.invertDir;
  digitalWrite(axis.dirPin, direction ? HIGH : LOW);

  axis.phase += fabsf(speed) * dt;
  while (axis.phase >= 1.0f) {
    digitalWrite(axis.stepPin, HIGH);
    delayMicroseconds(STEP_PULSE_US);
    digitalWrite(axis.stepPin, LOW);
    axis.phase -= 1.0f;
  }
}

static void updateMotors() {
  const uint32_t now = micros();
  if (lastMotorUpdateUs == 0) {
    lastMotorUpdateUs = now;
    return;
  }
  const uint32_t elapsedUs = now - lastMotorUpdateUs;
  if (elapsedUs < 250) {
    return;
  }
  lastMotorUpdateUs = now;

  if (!driverEnabled || digitalRead(ESTOP_PIN) == LOW) {
    stopMotion();
    if (digitalRead(ESTOP_PIN) == LOW) {
      triggerArmed = false;
      releaseTrigger();
      setDrivers(false);
    }
    return;
  }

  const float dt = elapsedUs / 1000000.0f;
  updateAxis(axisX, dt);
  updateAxis(axisY, dt);
}

static float commandToSps(long value, float maxSps) {
  value = constrain(value, -1000L, 1000L);
  return (static_cast<float>(value) / 1000.0f) * maxSps;
}

static void configureTmcDriver(TMC2209Stepper &driver, uint16_t runMa, uint16_t holdMa, bool spreadCycle) {
  driver.begin();
  delay(20);
  driver.rms_current(runMa, holdMa);
  driver.hold_multiplier(0.5);
  driver.iholddelay(1);
  driver.microsteps(MICROSTEPS);
  driver.intpol(true);
  driver.en_spreadCycle(spreadCycle);
  driver.TPWMTHRS(0);
  driver.toff(4);
  driver.blank_time(1);
  driver.hysteresis_start(5);
  driver.hysteresis_end(1);
  driver.pwm_autoscale(true);
  driver.TPOWERDOWN(2);
}

static void setupTmc() {
  Serial2.setTX(X_UART_TX);
  Serial2.setRX(X_UART_RX);
  UART_X.begin(115200);
  delay(30);

  Serial1.setTX(Y_UART_TX);
  Serial1.setRX(Y_UART_RX);
  UART_Y.begin(115200);
  delay(30);

  configureTmcDriver(driverX, X_RUN_CURRENT_MA, X_HOLD_CURRENT_MA, true);
  configureTmcDriver(driverY, Y_RUN_CURRENT_MA, Y_HOLD_CURRENT_MA, true);
}

static void processCommand(char *cmd) {
  lastCommandUs = micros();

  if (strcmp(cmd, "PING") == 0) {
    Serial.println("OK,PONG");
    return;
  }

  if (strcmp(cmd, "STAT") == 0) {
    Serial.print("OK,STAT,ESTOP=");
    Serial.print(digitalRead(ESTOP_PIN) == LOW ? 1 : 0);
    Serial.print(",DRV=");
    Serial.print(driverEnabled ? 1 : 0);
    Serial.print(",ARM=");
    Serial.println(triggerArmed ? 1 : 0);
    return;
  }

  if (strcmp(cmd, "STP") == 0) {
    stopMotion();
    Serial.println("OK,STOP");
    return;
  }

  if (strcmp(cmd, "TMC_STATUS") == 0) {
    Serial.print("TMC_X,DRV_STATUS=");
    Serial.println(driverX.DRV_STATUS(), HEX);
    Serial.print("TMC_Y,DRV_STATUS=");
    Serial.println(driverY.DRV_STATUS(), HEX);
    return;
  }

  char *command = strtok(cmd, ",");
  char *arg1 = strtok(nullptr, ",");
  char *arg2 = strtok(nullptr, ",");
  if (command == nullptr) {
    return;
  }

  if (strcmp(command, "DRV") == 0 && arg1 != nullptr) {
    const bool enabled = atoi(arg1) != 0;
    setDrivers(enabled);
    if (!enabled) {
      triggerArmed = false;
      releaseTrigger();
    }
    Serial.println(enabled ? "OK,DRIVER_ENABLED" : "OK,DRIVER_DISABLED");
    return;
  }

  if (strcmp(command, "ARM") == 0 && arg1 != nullptr) {
    const bool requested = atoi(arg1) != 0;
    if (requested && digitalRead(ESTOP_PIN) == LOW) {
      triggerArmed = false;
      releaseTrigger();
      Serial.println("ERR,ESTOP_ACTIVE");
      return;
    }
    triggerArmed = requested;
    releaseTrigger();
    Serial.println(triggerArmed ? "OK,ARM_1" : "OK,ARM_0");
    return;
  }

  if (strcmp(command, "SPD") == 0 && arg1 != nullptr && arg2 != nullptr) {
    axisX.targetSps = commandToSps(atol(arg1), axisX.maxSps);
    axisY.targetSps = commandToSps(atol(arg2), axisY.maxSps);
    Serial.println("OK,SPD");
    return;
  }

  if (strcmp(command, "CFG_SERVO") == 0 && arg1 != nullptr && arg2 != nullptr) {
    servoReleaseDeg = constrain(atoi(arg1), 0, 180);
    servoFireDeg = constrain(atoi(arg2), 0, 180);
    triggerServo.write(servoReleaseDeg);
    Serial.print("OK,SERVO_CFG,");
    Serial.print(servoReleaseDeg);
    Serial.print(",");
    Serial.println(servoFireDeg);
    return;
  }

  if (strcmp(command, "SERVO") == 0 && arg1 != nullptr) {
    Serial.println("ERR,SERVO_DIRECT_DISABLED");
    return;
  }

  if (strcmp(command, "LZR") == 0 && arg1 != nullptr) {
    stopMotion();
    if (atoi(arg1) != 0) {
      if (digitalRead(ESTOP_PIN) == LOW) {
        triggerArmed = false;
        releaseTrigger();
        Serial.println("ERR,ESTOP_ACTIVE");
        return;
      }
      if (!triggerArmed) {
        releaseTrigger();
        Serial.println("ERR,TRIGGER_NOT_ARMED");
        return;
      }
      triggerServo.write(servoFireDeg);
      triggerActive = true;
      triggerActivatedUs = micros();
      Serial.println("OK,LASER_1");
    } else {
      releaseTrigger();
      Serial.println("OK,LASER_0");
    }
    return;
  }

  Serial.print("ERR,UNKNOWN_CMD,");
  Serial.println(command);
}

static void pollSerial() {
  while (Serial.available() > 0) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\n' || c == '\r') {
      if (commandLength > 0) {
        commandBuffer[commandLength] = '\0';
        processCommand(commandBuffer);
        commandLength = 0;
      }
      continue;
    }
    if (commandLength < sizeof(commandBuffer) - 1) {
      commandBuffer[commandLength++] = c;
    } else {
      commandLength = 0;
      Serial.println("ERR,CMD_TOO_LONG");
    }
  }
}

static void checkWatchdog() {
  const uint32_t now = micros();

  // The host release command is still expected, but the Pico owns the final
  // pulse bound. A stalled backend can therefore never hold the trigger.
  if (triggerActive && triggerActivatedUs != 0 && now - triggerActivatedUs > TRIGGER_PULSE_TIMEOUT_US) {
    releaseTrigger();
  }

  // Logical idle arm is not a physical output. If motion or a trigger pulse
  // is active, loss of host commands must stop outputs and clear that arm.
  if ((driverEnabled || triggerActive) && lastCommandUs != 0 && now - lastCommandUs > WATCHDOG_TIMEOUT_US) {
    stopMotion();
    triggerArmed = false;
    releaseTrigger();
    setDrivers(false);
  }
}

void setup() {
  Serial.begin(460800);
  delay(300);

  pinMode(X_STEP_PIN, OUTPUT);
  pinMode(X_DIR_PIN, OUTPUT);
  pinMode(X_EN_PIN, OUTPUT);
  pinMode(Y_STEP_PIN, OUTPUT);
  pinMode(Y_DIR_PIN, OUTPUT);
  pinMode(Y_EN_PIN, OUTPUT);
  pinMode(ESTOP_PIN, INPUT_PULLUP);

  digitalWrite(X_STEP_PIN, LOW);
  digitalWrite(Y_STEP_PIN, LOW);
  setDrivers(false);

  triggerServo.attach(SERVO_PIN);
  triggerServo.write(servoReleaseDeg);

  setupTmc();

  lastCommandUs = micros();
  lastMotorUpdateUs = micros();
  Serial.println("OK,PICO_READY_CLEAN");
}

void loop() {
  pollSerial();
  updateMotors();
  checkWatchdog();
}
