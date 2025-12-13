"""
AI Agent - Tests
Unit tests for rule engine, explanation generator, and agent service.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from datetime import datetime
from crop_app.models import (
    FarmProfile, FieldPlot, SensorReading, 
    AnomalyEvent, AgentRecommendation
)
from ai_agent.rule_engine import (
    RuleEngine, RuleContext, 
    IrrigationFailureRule, HeatStressRule
)
from ai_agent.explanation_generator import ExplanationGenerator
from ai_agent.agent_service import AgentRecommendationService


class RuleEngineTests(TestCase):
    """Test rule engine functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = RuleEngine()
    
    def test_irrigation_failure_rule(self):
        """Test irrigation failure detection."""
        context = RuleContext(
            anomaly_type='moisture_anomaly',
            severity='HIGH',
            model_confidence=0.85,
            sensor_type='moisture',
            plot_id=1,
            recent_values=[65.0, 60.0, 52.0, 45.0],
            timestamp=datetime.now()
        )
        
        result = self.engine.evaluate(context)
        
        self.assertIsNotNone(result)
        self.assertIn('irrigation', result['action'])
        self.assertEqual(result['urgency'], 'high')
        self.assertGreater(result['confidence'], 0.8)
    
    def test_heat_stress_rule(self):
        """Test heat stress detection."""
        context = RuleContext(
            anomaly_type='temperature_anomaly',
            severity='CRITICAL',
            model_confidence=0.92,
            sensor_type='temperature',
            plot_id=1,
            recent_values=[28.0, 32.0, 35.0, 38.0],
            timestamp=datetime.now()
        )
        
        result = self.engine.evaluate(context)
        
        self.assertIsNotNone(result)
        self.assertIn('heat', result['action'])
        self.assertEqual(result['urgency'], 'high')
    
    def test_low_confidence_rule(self):
        """Test low confidence handling."""
        context = RuleContext(
            anomaly_type='moisture_anomaly',
            severity='MEDIUM',
            model_confidence=0.5,  # Low confidence
            sensor_type='moisture',
            plot_id=1,
            recent_values=[50.0, 48.0, 47.0],
            timestamp=datetime.now()
        )
        
        result = self.engine.evaluate(context)
        
        self.assertIsNotNone(result)
        self.assertIn('manual', result['action'])
        self.assertEqual(result['urgency'], 'low')
    
    def test_multiple_anomalies(self):
        """Test multiple simultaneous anomalies."""
        contexts = [
            RuleContext(
                anomaly_type='moisture_anomaly',
                severity='HIGH',
                model_confidence=0.85,
                sensor_type='moisture',
                plot_id=1,
                recent_values=[50.0],
                timestamp=datetime.now()
            ),
            RuleContext(
                anomaly_type='temperature_anomaly',
                severity='CRITICAL',
                model_confidence=0.90,
                sensor_type='temperature',
                plot_id=1,
                recent_values=[35.0],
                timestamp=datetime.now()
            )
        ]
        
        result = self.engine.evaluate_multiple_anomalies(contexts)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['rule_name'], 'multiple_anomaly')
        self.assertEqual(result['urgency'], 'high')


class ExplanationGeneratorTests(TestCase):
    """Test explanation generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = ExplanationGenerator()
    
    def test_irrigation_explanation(self):
        """Test irrigation failure explanation."""
        anomaly = {
            'timestamp': datetime.now(),
            'anomaly_type': 'moisture_anomaly',
            'severity': 'HIGH',
            'model_confidence': 0.85
        }
        
        recommendation = {
            'action': 'immediate_irrigation_check',
            'description': 'Check irrigation system immediately',
            'urgency': 'high',
            'confidence': 0.95,
            'reasoning': 'Soil moisture dropped rapidly',
            'details': {'drop_percentage': 15.2}
        }
        
        explanation = self.generator.generate_explanation(
            anomaly, recommendation
        )
        
        self.assertIn('moisture anomaly', explanation.lower())
        self.assertIn('immediate action required', explanation.lower())
        self.assertIn('confidence', explanation.lower())
    
    def test_summary_generation(self):
        """Test summary generation."""
        recommendation = {
            'description': 'Check irrigation system',
            'urgency': 'high'
        }
        
        summary = self.generator.generate_summary(recommendation)
        
        self.assertIn('🔴', summary)  # High urgency emoji
        self.assertIn('Check irrigation', summary)


class AgentServiceTests(TestCase):
    """Test agent service integration."""
    
    def setUp(self):
        """Set up test database."""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create farm
        self.farm = FarmProfile.objects.create(
            owner=self.user,
            location='Test Farm',
            size=10.0,
            crop_type='Wheat'
        )
        
        # Create plot
        self.plot = FieldPlot.objects.create(
            farm=self.farm,
            crop_variety='Test Variety',
            plot_name='Plot 1'
        )
        
        # Create sensor readings
        for i in range(10):
            SensorReading.objects.create(
                plot=self.plot,
                sensor_type='moisture',
                value=60.0 - (i * 2),  # Decreasing moisture
                source='test'
            )
        
        # Create anomaly
        self.anomaly = AnomalyEvent.objects.create(
            plot=self.plot,
            anomaly_type='moisture_anomaly',
            severity='HIGH',
            model_confidence=0.85
        )
        
        # Initialize service
        self.service = AgentRecommendationService()
    
    def test_create_recommendation(self):
        """Test recommendation creation."""
        recommendation = self.service.create_recommendation_for_anomaly(
            self.anomaly
        )
        
        self.assertIsNotNone(recommendation)
        self.assertIsInstance(recommendation, AgentRecommendation)
        self.assertEqual(recommendation.anomaly_event, self.anomaly)
        self.assertIsNotNone(recommendation.explanation_text)
        self.assertGreater(recommendation.confidence, 0)
    
    def test_duplicate_recommendation_prevention(self):
        """Test that duplicate recommendations aren't created."""
        # Create first recommendation
        rec1 = self.service.create_recommendation_for_anomaly(self.anomaly)
        
        # Try to create again
        rec2 = self.service.create_recommendation_for_anomaly(self.anomaly)
        
        # Should return existing recommendation
        self.assertEqual(rec1.id, rec2.id)
    
    def test_get_plot_recommendations(self):
        """Test getting recommendations for a plot."""
        # Create recommendation
        self.service.create_recommendation_for_anomaly(self.anomaly)
        
        # Get recommendations
        recommendations = self.service.get_recommendations_for_plot(
            self.plot.id,
            limit=10
        )
        
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]['anomaly']['id'], self.anomaly.id)
    
    def test_batch_processing(self):
        """Test batch processing of unprocessed anomalies."""
        # Create multiple anomalies
        for i in range(3):
            AnomalyEvent.objects.create(
                plot=self.plot,
                anomaly_type=f'test_anomaly_{i}',
                severity='MEDIUM',
                model_confidence=0.7
            )
        
        # Batch process
        stats = self.service.batch_process_unprocessed_anomalies()
        
        self.assertGreater(stats['total_unprocessed'], 0)
        self.assertGreater(stats['processed'], 0)


class SignalTests(TestCase):
    """Test Django signals."""
    
    def setUp(self):
        """Set up test database."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.farm = FarmProfile.objects.create(
            owner=self.user,
            location='Test Farm',
            size=10.0,
            crop_type='Wheat'
        )
        
        self.plot = FieldPlot.objects.create(
            farm=self.farm,
            crop_variety='Test Variety'
        )
    
    def test_signal_creates_recommendation(self):
        """Test that signal automatically creates recommendation."""
        # Create anomaly (signal should trigger)
        anomaly = AnomalyEvent.objects.create(
            plot=self.plot,
            anomaly_type='moisture_anomaly',
            severity='HIGH',
            model_confidence=0.85
        )
        
        # Check that recommendation was created
        self.assertTrue(hasattr(anomaly, 'recommendation'))
        self.assertIsNotNone(anomaly.recommendation)


# Run tests with: python manage.py test ai_agent
if __name__ == '__main__':
    import django
    django.setup()
    
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    test_runner.run_tests(['ai_agent'])