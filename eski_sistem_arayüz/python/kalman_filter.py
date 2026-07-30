# kalman_filter.py - Kalman Filter pozisyon tahmini (OpenCV)
import cv2
import numpy as np
import logging
from typing import Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KalmanFilter:
    """
    Constant velocity Kalman Filter: state [x, y, vx, vy]
    Measurement: [x, y]
    Adaptasyon: laser_guided_object_tracker/utils.py
    """
    def __init__(self, dt: float = 1/30.0):  # 30 FPS default
        self.dt = dt
        self.kf = cv2.KalmanFilter(4, 2)  # 4 state, 2 measurement

        # Transition matrix F (constant velocity)
        self.kf.transitionMatrix = np.array([
            [1, 0, self.dt, 0],
            [0, 1, 0, self.dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], np.float32)

        # Measurement matrix H
        self.kf.measurementMatrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], np.float32)

        # Process noise covariance Q
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03

        # Measurement noise covariance R
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 1.0

        # Initial error covariance P
        self.kf.errorCovPost = np.eye(4, dtype=np.float32)

        # Initialized flag
        self.initialized = False

    def predict(self) -> np.ndarray:
        """Tahmin et (state vector)"""
        pred_state = self.kf.predict()
        return pred_state

    def update(self, measurement: np.ndarray) -> np.ndarray:
        """Ölçümle güncelle (2x1 array [x,y])"""
        meas = np.array([[np.float32(measurement[0])],
                         [np.float32(measurement[1])]], dtype=np.float32)
        self.kf.correct(meas)
        self.initialized = True
        return self.kf.statePost

    def predict_ahead(self, steps: int = 1) -> Tuple[float, float]:
        """
        İleri tahmin: N frame ahead
        Yaklaşık: current velocity * steps * dt
        """
        if not self.initialized:
            return 0.0, 0.0

        state = self.kf.statePost.flatten()
        x, y, vx, vy = state
        pred_x = x + vx * steps * self.dt
        pred_y = y + vy * steps * self.dt
        return pred_x, pred_y

    def get_position(self) -> Tuple[float, float]:
        """Güncel tahmin pozisyon"""
        if not self.initialized:
            return 0.0, 0.0
        state = self.kf.statePost.flatten()
        return state[0], state[1]

    def reset(self):
        """Yeni hedef için reset"""
        self.initialized = False
        self.kf.errorCovPost = np.eye(4, dtype=np.float32)