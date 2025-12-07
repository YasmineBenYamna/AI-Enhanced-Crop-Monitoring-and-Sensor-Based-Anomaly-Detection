"""
ML Module for Crop Monitoring System
Provides anomaly detection using Isolation Forest algorithm.
"""

__version__ = '1.0.0'
__author__ = 'DS2 2025-2026 Project'

# Make key classes easily importable
from .anomaly_detector import IsolationForestDetector
from .preprocessing import SensorDataPreprocessor

__all__ = [
    'IsolationForestDetector',
    'SensorDataPreprocessor',
]