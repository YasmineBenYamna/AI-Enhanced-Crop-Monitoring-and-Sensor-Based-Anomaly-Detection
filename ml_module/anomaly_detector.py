"""
ML Module - Isolation Forest Anomaly Detector
Detects anomalies in sensor data using Isolation Forest algorithm.
"""

from sklearn.ensemble import IsolationForest
import numpy as np
from typing import Dict, List, Tuple
import pickle
import os
from datetime import datetime


class IsolationForestDetector:
    """
    Anomaly detector using Isolation Forest algorithm.
    Detects unusual patterns in agricultural sensor data.
    """
    
    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        """
        Initialize the Isolation Forest detector.
        
        Args:
            contamination: Expected proportion of anomalies (0.0-0.5)
                          0.1 = expect 10% of data to be anomalies
            random_state: Random seed for reproducibility
        """
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100,
            max_samples='auto',
            max_features=1.0,
            bootstrap=False,
            n_jobs=-1,
            verbose=0
        )
        self.is_trained = False
        self.training_data_size = 0
        self.training_date = None
    
    def train(self, normal_data: np.ndarray) -> Dict:
        """
        Train the Isolation Forest on normal sensor data.
        
        Args:
            normal_data: Array of normal readings (n_samples, n_features)
                        Should contain ONLY normal data (no anomalies)
        
        Returns:
            Training statistics dictionary
        """
        if normal_data.shape[0] < 10:
            raise ValueError(
                f"Need at least 10 samples for training, got {normal_data.shape[0]}"
            )
        
        # Train the model
        self.model.fit(normal_data)
        
        # Mark as trained
        self.is_trained = True
        self.training_data_size = normal_data.shape[0]
        self.training_date = datetime.now()
        
        # Get training statistics
        training_scores = self.model.score_samples(normal_data)
        
        stats = {
            'trained': True,
            'n_samples': normal_data.shape[0],
            'n_features': normal_data.shape[1],
            'training_date': self.training_date.isoformat(),
            'mean_score': float(np.mean(training_scores)),
            'std_score': float(np.std(training_scores)),
            'min_score': float(np.min(training_scores)),
            'max_score': float(np.max(training_scores))
        }
        
        return stats
    
    def predict(self, data: np.ndarray) -> np.ndarray:
        """
        Predict if data points are anomalies.
        
        Args:
            data: Array of sensor readings (n_samples, n_features)
        
        Returns:
            Array of predictions: 1 = normal, -1 = anomaly
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet! Call train() first.")
        
        predictions = self.model.predict(data)
        return predictions
    
    def get_anomaly_scores(self, data: np.ndarray) -> np.ndarray:
        """
        Get anomaly scores for data points.
        Lower (more negative) scores = more anomalous
        
        Args:
            data: Array of sensor readings (n_samples, n_features)
        
        Returns:
            Array of anomaly scores
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet! Call train() first.")
        
        scores = self.model.score_samples(data)
        return scores
    
    def detect_with_confidence(self, data: np.ndarray) -> List[Dict]:
        """
        Detect anomalies with confidence scores.
        
        Args:
            data: Array of sensor readings (n_samples, n_features)
        
        Returns:
            List of detection results with confidence
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet! Call train() first.")
        
        # Get predictions and scores
        predictions = self.predict(data)
        scores = self.get_anomaly_scores(data)
        
        results = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            is_anomaly = (pred == -1)
            
            # Convert score to confidence (0-1 range)
            if is_anomaly:
                confidence = min(1.0, abs(score) / 0.5)
            else:
                confidence = min(1.0, score / 0.5) if score > 0 else 0.0
            
            results.append({
                'index': i,
                'is_anomaly': is_anomaly,
                'anomaly_score': float(score),
                'confidence': float(confidence),
                'severity': self._calculate_severity(score, is_anomaly)
            })
        
        return results
    
    def _calculate_severity(self, score: float, is_anomaly: bool) -> str:
        """
        Calculate severity level based on anomaly score.
        
        Args:
            score: Anomaly score from model
            is_anomaly: Whether point is classified as anomaly
        
        Returns:
            Severity level: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'NORMAL'
        """
        if not is_anomaly:
            return 'NORMAL'
        
        # More negative = more severe
        if score < -0.4:
            return 'CRITICAL'
        elif score < -0.3:
            return 'HIGH'
        elif score < -0.2:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def save_model(self, filepath: str):
        """
        Save trained model to file.
        
        Args:
            filepath: Path to save the model
        """
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        # Save all necessary data
        model_data = {
            'model': self.model,
            'is_trained': self.is_trained,
            'training_data_size': self.training_data_size,
            'training_date': self.training_date,
            'contamination': self.model.contamination,
            'random_state': self.model.random_state
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"✅ Model saved to: {filepath}")
    
    @classmethod
    def load_model(cls, filepath: str):
        """
        Load trained model from file (CLASS METHOD).
        
        Args:
            filepath: Path to the saved model
            
        Returns:
            IsolationForestDetector: Loaded detector instance
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        # Create new instance
        contamination = model_data.get('contamination', 0.1)
        random_state = model_data.get('random_state', 42)
        detector = cls(contamination=contamination, random_state=random_state)
        
        # Restore saved state
        detector.model = model_data['model']
        detector.is_trained = model_data['is_trained']
        detector.training_data_size = model_data['training_data_size']
        detector.training_date = model_data['training_date']
        
        print(f"✅ Model loaded from: {filepath}")
        print(f"   Trained: {detector.is_trained}")
        print(f"   Training size: {detector.training_data_size} samples")
        print(f"   Training date: {detector.training_date}")
        
        return detector


class AnomalyDetectionService:
    """
    High-level service for anomaly detection in agricultural data.
    Integrates preprocessing and Isolation Forest detection.
    """
    
    def __init__(self, detector: IsolationForestDetector = None):
        """
        Initialize the detection service.
        
        Args:
            detector: Pre-trained IsolationForestDetector (optional)
        """
        from .preprocessing import SensorDataPreprocessor
        
        self.detector = detector if detector else IsolationForestDetector()
        self.preprocessor = SensorDataPreprocessor(window_size=10)
    
    def detect_anomalies(self, plot_id: int, sensor_type: str) -> List[Dict]:
        """
        Detect anomalies for a specific plot and sensor.
        
        Args:
            plot_id: Plot identifier
            sensor_type: Sensor type (moisture, temperature, humidity)
        
        Returns:
            List of anomaly detection results
        """
        from .preprocessing import get_recent_readings
        
        # Get recent readings
        values = get_recent_readings(plot_id, sensor_type, count=50)
        
        if len(values) < 10:
            return [{
                'error': 'Not enough data',
                'message': f'Need at least 10 readings, have {len(values)}'
            }]
        
        # Preprocess
        processed_data = self.preprocessor.prepare_for_model(values, use_features=True)
        
        # Detect anomalies
        results = self.detector.detect_with_confidence(processed_data)
        
        # Add context
        for result in results:
            result['plot_id'] = plot_id
            result['sensor_type'] = sensor_type
            result['timestamp'] = datetime.now().isoformat()
        
        return results


# Example usage and testing
if __name__ == '__main__':
    print("Testing Isolation Forest Anomaly Detector...")
    
    # Generate synthetic training data (normal)
    print("\n1. Generating training data (normal patterns)...")
    np.random.seed(42)
    normal_data = np.random.randn(100, 5) * 0.5
    print(f"   Training data shape: {normal_data.shape}")
    
    # Create and train detector
    print("\n2. Training Isolation Forest...")
    detector = IsolationForestDetector(contamination=0.1)
    stats = detector.train(normal_data)
    print(f"   ✅ Training completed!")
    print(f"   Samples: {stats['n_samples']}")
    print(f"   Features: {stats['n_features']}")
    print(f"   Mean score: {stats['mean_score']:.4f}")
    
    # Test on normal data
    print("\n3. Testing on normal data...")
    test_normal = np.random.randn(10, 5) * 0.5
    results_normal = detector.detect_with_confidence(test_normal)
    anomalies_normal = sum(1 for r in results_normal if r['is_anomaly'])
    print(f"   Detected {anomalies_normal}/10 as anomalies (should be ~1)")
    
    # Test on anomalous data
    print("\n4. Testing on anomalous data...")
    test_anomaly = np.random.randn(10, 5) * 3.0
    results_anomaly = detector.detect_with_confidence(test_anomaly)
    anomalies_detected = sum(1 for r in results_anomaly if r['is_anomaly'])
    print(f"   Detected {anomalies_detected}/10 as anomalies (should be ~8-10)")
    
    # Show example detection
    print("\n5. Example detection result:")
    if results_anomaly:
        example = results_anomaly[0]
        print(f"   Is anomaly: {example['is_anomaly']}")
        print(f"   Confidence: {example['confidence']:.2f}")
        print(f"   Severity: {example['severity']}")
        print(f"   Score: {example['anomaly_score']:.4f}")
    
    # Test model save/load
    print("\n6. Testing model save/load...")
    detector.save_model('/tmp/test_model.pkl')
    
    # ✅ Now load_model is a class method
    detector2 = IsolationForestDetector.load_model('/tmp/test_model.pkl')
    print(f"   ✅ Model loaded successfully!")
    print(f"   Is trained: {detector2.is_trained}")
    
    # Test loaded model
    print("\n7. Testing loaded model...")
    test_results = detector2.detect_with_confidence(test_anomaly)
    print(f"   Loaded model detected {sum(1 for r in test_results if r['is_anomaly'])}/10 anomalies")
    
    print("\n✅ All tests completed!")