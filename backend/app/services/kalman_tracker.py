"""
Kalman Tracker — Eski sistemden (eski_sistem_arayüz/python/kalman_filter.py) uyarlandı.

Constant-velocity Kalman filter: state [x, y, vx, vy], measurement [x, y].
OpenCV cv2.KalmanFilter kullanır (backend'de opencv-headless mevcut).
Hedef kaybolduğunda pozisyon tahmini sağlar.
"""

from __future__ import annotations

import cv2
import numpy as np


class KalmanTracker:
    """
    Constant velocity Kalman Filter: state [x, y, vx, vy].
    Measurement: [x, y].

    Eski sistemdeki ``KalmanFilter`` sınıfının birebir karşılığı.
    """

    def __init__(self, dt: float = 1 / 30.0) -> None:
        self.dt = dt
        self.kf = cv2.KalmanFilter(4, 2)

        # Transition matrix F (constant velocity)
        self.kf.transitionMatrix = np.array(
            [
                [1, 0, self.dt, 0],
                [0, 1, 0, self.dt],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ],
            np.float32,
        )

        # Measurement matrix H
        self.kf.measurementMatrix = np.array(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
            ],
            np.float32,
        )

        # Process noise covariance Q
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03

        # Measurement noise covariance R
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 1.0

        # Initial error covariance P
        self.kf.errorCovPost = np.eye(4, dtype=np.float32)

        self.initialized = False

    def predict(self) -> tuple[float, float]:
        """
        Tahmin et — hedef kaybolduğunda Kalman öngörüsü kullanılır.

        Returns
        -------
        (predicted_x, predicted_y)
        """
        pred_state = self.kf.predict()
        return float(pred_state[0][0]), float(pred_state[1][0])

    def update(self, x: float, y: float) -> tuple[float, float]:
        """
        Yeni ölçüm ile güncelle.

        Parameters
        ----------
        x, y : hedef merkez koordinatları (piksel)

        Returns
        -------
        (corrected_x, corrected_y)
        """
        if not self.initialized:
            initial = np.array([[np.float32(x)], [np.float32(y)], [0.0], [0.0]], dtype=np.float32)
            self.kf.statePre = initial.copy()
            self.kf.statePost = initial.copy()
            self.initialized = True
            return float(x), float(y)
        meas = np.array([[np.float32(x)], [np.float32(y)]], dtype=np.float32)
        self.kf.correct(meas)
        state = self.kf.statePost.flatten()
        return float(state[0]), float(state[1])

    def predict_ahead(self, steps: int = 1) -> tuple[float, float]:
        """İleri tahmin: N frame ahead."""
        if not self.initialized:
            return 0.0, 0.0
        state = self.kf.statePost.flatten()
        x, y, vx, vy = state
        return float(x + vx * steps * self.dt), float(y + vy * steps * self.dt)

    def get_position(self) -> tuple[float, float]:
        """Güncel tahmin pozisyon."""
        if not self.initialized:
            return 0.0, 0.0
        state = self.kf.statePost.flatten()
        return float(state[0]), float(state[1])

    def reset(self) -> None:
        """Yeni hedef için Kalman state'ini sıfırla."""
        self.initialized = False
        self.kf.errorCovPost = np.eye(4, dtype=np.float32)
        self.kf.statePost = np.zeros((4, 1), dtype=np.float32)
