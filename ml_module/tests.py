"""
ML Module - Unit Tests
Tests for Isolation Forest anomaly detection.
"""

from django.test import TestCase
import numpy as np
from .anomaly_detector import IsolationForestDetector
from .preprocessing import SensorDataPreprocessor


class IsolationForestDetectorTests(TestCase):
    """Test cases for Isolation Forest detector."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = IsolationForestDetector(contamination=0.1)
        
    def test_detector_initialization(self):
        """Test detector is initialized correctly."""
        self.assertIsNotNone(self.detector.model)
        self.assertFalse(self.detector.is_trained)
        self.assertEqual(self.detector.training_data_size, 0)
    
    def test_training_with_valid_data(self):
        """Test training with valid normal data."""
        # Generate normal training data
        normal_data = np.random.randn(100, 5) * 0.5
        
        # Train model
        stats = self.detector.train(normal_data)
        
        # Assertions
        self.assertTrue(self.detector.is_trained)
        self.assertEqual(stats['n_samples'], 100)
        self.assertEqual(stats['n_features'], 5)
        self.assertIn('mean_score', stats)
    
    def test_training_with_insufficient_data(self):
        """Test training fails with too few samples."""
        insufficient_data = np.random.randn(5, 5)
        
        with self.assertRaises(ValueError):
            self.detector.train(insufficient_data)
    
    def test_prediction_before_training(self):
        """Test prediction fails if model not trained."""
        test_data = np.random.randn(10, 5)
        
        with self.assertRaises(ValueError):
            self.detector.predict(test_data)
    
    def test_prediction_after_training(self):
        """Test prediction works after training."""
        # Train
        normal_data = np.random.randn(100, 5) * 0.5
        self.detector.train(normal_data)
        
        # Test
        test_data = np.random.randn(10, 5) * 0.5
        predictions = self.detector.predict(test_data)
        
        # Assertions
        self.assertEqual(len(predictions), 10)
        self.assertTrue(all(p in [1, -1] for p in predictions))
    
    def test_anomaly_detection_on_normal_data(self):
        """Test few anomalies detected in normal data."""
        # Train on normal
        normal_train = np.random.randn(100, 5) * 0.5
        self.detector.train(normal_train)
        
        # Test on normal
        normal_test = np.random.randn(20, 5) * 0.5
        results = self.detector.detect_with_confidence(normal_test)
        
        anomalies = sum(1 for r in results if r['is_anomaly'])
        
        # Should detect 0-4 anomalies in normal data (< 20%)
        self.assertLess(anomalies, 5)
    
    def test_anomaly_detection_on_anomalous_data(self):
        """Test many anomalies detected in anomalous data."""
        # Train on normal
        normal_train = np.random.randn(100, 5) * 0.5
        self.detector.train(normal_train)
        
        # Test on anomalous (much larger variance)
        anomalous_test = np.random.randn(20, 5) * 3.0
        results = self.detector.detect_with_confidence(anomalous_test)
        
        anomalies = sum(1 for r in results if r['is_anomaly'])
        
        # Should detect 10+ anomalies in anomalous data (> 50%)
        self.assertGreater(anomalies, 10)
    
    def test_confidence_scores(self):
        """Test confidence scores are in valid range."""
        # Train
        normal_data = np.random.randn(100, 5) * 0.5
        self.detector.train(normal_data)
        
        # Test
        test_data = np.random.randn(10, 5)
        results = self.detector.detect_with_confidence(test_data)
        
        # Check confidence is between 0 and 1
        for result in results:
            self.assertGreaterEqual(result['confidence'], 0.0)
            self.assertLessEqual(result['confidence'], 1.0)
    
    def test_severity_levels(self):
        """Test severity levels are correct."""
        # Train
        normal_data = np.random.randn(100, 5) * 0.5
        self.detector.train(normal_data)
        
        # Test
        test_data = np.random.randn(10, 5) * 3.0
        results = self.detector.detect_with_confidence(test_data)
        
        valid_severities = ['NORMAL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        
        for result in results:
            self.assertIn(result['severity'], valid_severities)


class SensorDataPreprocessorTests(TestCase):
    """Test cases for sensor data preprocessing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.preprocessor = SensorDataPreprocessor(window_size=5)
    
    def test_preprocessor_initialization(self):
        """Test preprocessor initializes correctly."""
        self.assertEqual(self.preprocessor.window_size, 5)
        self.assertIsNotNone(self.preprocessor.scaler)
    
    def test_window_creation(self):
        """Test sliding window creation."""
        values = [10, 20, 30, 40, 50, 60, 70]
        windows = self.preprocessor.create_windows(values)
        
        # Should create 3 windows of size 5
        self.assertEqual(len(windows), 3)
        self.assertEqual(windows.shape[1], 5)
        
        # First window should be [10, 20, 30, 40, 50]
        np.testing.assert_array_equal(windows[0], [10, 20, 30, 40, 50])
    
    def test_window_creation_insufficient_data(self):
        """Test window creation fails with insufficient data."""
        values = [10, 20, 30]  # Only 3 values, need 5
        
        with self.assertRaises(ValueError):
            self.preprocessor.create_windows(values)
    
    def test_feature_extraction(self):
        """Test statistical feature extraction."""
        window = np.array([10, 20, 30, 40, 50])
        features = self.preprocessor.calculate_features(window)
        
        # Should return 5 features: mean, std, min, max, range
        self.assertEqual(len(features), 5)
        
        # Check values
        self.assertAlmostEqual(features[0], 30.0)  # mean
        self.assertAlmostEqual(features[2], 10.0)  # min
        self.assertAlmostEqual(features[3], 50.0)  # max
        self.assertAlmostEqual(features[4], 40.0)  # range
    
    def test_rapid_change_detection(self):
        """Test rapid change detection."""
        # Normal gradual change
        normal_values = [60, 59, 58, 57, 56]
        has_change, max_change = self.preprocessor.check_rapid_change(normal_values, threshold_percent=10.0)
        self.assertFalse(has_change)
        
        # Rapid change
        rapid_values = [60, 58, 40, 38, 36]
        has_change, max_change = self.preprocessor.check_rapid_change(rapid_values, threshold_percent=10.0)
        self.assertTrue(has_change)
        self.assertGreater(max_change, 10.0)
    
    def test_full_preprocessing_pipeline(self):
        """Test complete preprocessing pipeline."""
        values = list(range(50, 70))  # 20 values
        
        processed = self.preprocessor.prepare_for_model(values, use_features=True)
        
        # Should create windows and extract features
        self.assertEqual(processed.shape[1], 5)  # 5 features per window
        self.assertGreater(processed.shape[0], 0)  # At least some windows


class MLAPITests(TestCase):
    """Test cases for ML API endpoints."""
    
    def test_model_status_endpoint(self):
        """Test model status endpoint."""
        response = self.client.get('/api/ml/status/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have status for all sensor types
        self.assertIn('moisture', data)
        self.assertIn('temperature', data)
        self.assertIn('humidity', data)


# Run tests with: python manage.py test ml_module