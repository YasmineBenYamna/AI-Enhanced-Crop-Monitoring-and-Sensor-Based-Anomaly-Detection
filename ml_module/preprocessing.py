"""
ML Module - Data Preprocessing
Handles normalization and windowing for anomaly detection.
"""

import numpy as np
from sklearn.preprocessing import StandardScaler
from typing import List, Tuple
import pandas as pd


class SensorDataPreprocessor:
    """
    Preprocesses sensor data for ML model input.
    Handles normalization and time-window creation.
    """
    
    def __init__(self, window_size: int = 10):
        """
        Initialize the preprocessor.
        
        Args:
            window_size: Number of consecutive readings in each window
        """
        self.window_size = window_size
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def normalize(self, data: np.ndarray, fit: bool = False) -> np.ndarray:
        """
        Normalize data using StandardScaler (mean=0, std=1).
        
        Args:
            data: Input data array (n_samples, n_features)
            fit: Whether to fit the scaler (True for training data)
            
        Returns:
            Normalized data
        """
        # Reshape if 1D
        if data.ndim == 1:
            data = data.reshape(-1, 1)
        
        if fit:
            # Fit and transform (for training data)
            normalized = self.scaler.fit_transform(data)
            self.is_fitted = True
        else:
            # Only transform (for new data)
            if not self.is_fitted:
                raise ValueError("Scaler not fitted yet. Use fit=True first.")
            normalized = self.scaler.transform(data)
        
        return normalized
    
    def create_windows(self, values: List[float]) -> np.ndarray:
        """
        Create sliding time windows from sensor readings.
        
        Example:
            values = [60, 58, 56, 55, 40]
            window_size = 3
            Result: [[60, 58, 56], [58, 56, 55], [56, 55, 40]]
        
        Args:
            values: List of sensor values
            
        Returns:
            Array of windows (n_windows, window_size)
        """
        if len(values) < self.window_size:
            raise ValueError(
                f"Not enough data points. Need at least {self.window_size}, "
                f"got {len(values)}"
            )
        
        windows = []
        for i in range(len(values) - self.window_size + 1):
            window = values[i:i + self.window_size]
            windows.append(window)
        
        return np.array(windows)
    
    def calculate_features(self, window: np.ndarray) -> np.ndarray:
        """
        Calculate statistical features from a window.
        Features: mean, std, min, max, range
        
        Args:
            window: Single window of data
            
        Returns:
            Feature vector
        """
        features = [
            np.mean(window),      # Average value
            np.std(window),       # Variability
            np.min(window),       # Minimum
            np.max(window),       # Maximum
            np.max(window) - np.min(window),  # Range
        ]
        return np.array(features)
    
    def prepare_for_model(self, values: List[float], 
                         use_features: bool = True) -> np.ndarray:
        """
        Complete preprocessing pipeline: windowing + optional feature extraction.
        
        Args:
            values: List of sensor values
            use_features: If True, extract statistical features from windows
            
        Returns:
            Preprocessed data ready for model
        """
        # Create windows
        windows = self.create_windows(values)
        
        if use_features:
            # Extract features from each window
            feature_vectors = []
            for window in windows:
                features = self.calculate_features(window)
                feature_vectors.append(features)
            return np.array(feature_vectors)
        else:
            # Use raw windows
            return windows
    
    def check_rapid_change(self, values: List[float], 
                          threshold_percent: float = 15.0) -> Tuple[bool, float]:
        """
        Check for rapid changes in sensor values (useful for drops/spikes).
        
        Args:
            values: Recent sensor values
            threshold_percent: Percentage change threshold
            
        Returns:
            (has_rapid_change, max_change_percent)
        """
        if len(values) < 2:
            return False, 0.0
        
        # Calculate percentage changes
        changes = []
        for i in range(1, len(values)):
            if values[i-1] != 0:  # Avoid division by zero
                change_percent = abs((values[i] - values[i-1]) / values[i-1]) * 100
                changes.append(change_percent)
        
        if not changes:
            return False, 0.0
        
        max_change = max(changes)
        has_rapid_change = max_change >= threshold_percent
        
        return has_rapid_change, max_change


# Utility functions for quick access

def get_recent_readings(plot_id: int, sensor_type: str, 
                       count: int = 50) -> List[float]:
    """
    Get recent sensor readings from database.
    
    Args:
        plot_id: Plot identifier
        sensor_type: Sensor type (moisture, temperature, humidity)
        count: Number of recent readings to retrieve
        
    Returns:
        List of sensor values (most recent first)
    """
    from crop_app.models import SensorReading
    
    readings = SensorReading.objects.filter(
        plot_id=plot_id,
        sensor_type=sensor_type
    ).order_by('-timestamp')[:count]
    
    # Extract values and reverse (oldest to newest for windowing)
    values = [r.value for r in reversed(readings)]
    
    return values


def preprocess_sensor_data(plot_id: int, sensor_type: str,
                          window_size: int = 10) -> np.ndarray:
    """
    Complete preprocessing: fetch data + create windows + normalize.
    
    Args:
        plot_id: Plot identifier
        sensor_type: Sensor type
        window_size: Window size for time series
        
    Returns:
        Preprocessed data ready for Isolation Forest
    """
    # Get recent readings
    values = get_recent_readings(plot_id, sensor_type, count=50)
    
    if len(values) < window_size:
        raise ValueError(f"Not enough data. Need {window_size}, have {len(values)}")
    
    # Preprocess
    preprocessor = SensorDataPreprocessor(window_size=window_size)
    
    # Create windows with features
    processed_data = preprocessor.prepare_for_model(values, use_features=True)
    
    return processed_data


# Example usage
if __name__ == '__main__':
    # Test the preprocessor
    print("Testing SensorDataPreprocessor...")
    
    # Simulate some sensor readings
    test_values = [60, 58, 56, 55, 54, 52, 50, 48, 35, 33, 32, 30]
    
    preprocessor = SensorDataPreprocessor(window_size=5)
    
    # Test windowing
    print("\n1. Creating windows:")
    windows = preprocessor.create_windows(test_values)
    print(f"   Input: {test_values}")
    print(f"   Windows shape: {windows.shape}")
    print(f"   First window: {windows[0]}")
    
    # Test feature extraction
    print("\n2. Extracting features:")
    features = preprocessor.calculate_features(windows[0])
    print(f"   Features (mean, std, min, max, range): {features}")
    
    # Test rapid change detection
    print("\n3. Checking for rapid changes:")
    has_change, max_change = preprocessor.check_rapid_change(test_values)
    print(f"   Rapid change detected: {has_change}")
    print(f"   Maximum change: {max_change:.2f}%")
    
    # Test full pipeline
    print("\n4. Full preprocessing pipeline:")
    processed = preprocessor.prepare_for_model(test_values, use_features=True)
    print(f"   Processed data shape: {processed.shape}")
    print(f"   First feature vector: {processed[0]}")
    
    print("\n✅ Preprocessing tests completed!")