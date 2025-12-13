"""
AI Agent - Agent Service
Main orchestration service for agent recommendations.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone

from crop_app.models import AnomalyEvent, AgentRecommendation, SensorReading
from .rule_engine import RuleEngine, RuleContext
from .explanation_generator import ExplanationGenerator


class AgentDecisionEngine:
    """
    Core decision engine that processes anomalies and generates recommendations.
    """
    
    def __init__(self):
        self.rule_engine = RuleEngine()
        self.explanation_generator = ExplanationGenerator()
    
    def process_anomaly(self, anomaly_event: AnomalyEvent) -> Dict:
        """
        Process a single anomaly and generate recommendation.
        
        Args:
            anomaly_event: The anomaly event to process
            
        Returns:
            Dictionary with recommendation details
        """
        # Extract sensor type from anomaly type
        sensor_type = self._extract_sensor_type(anomaly_event.anomaly_type)
        
        # Get recent sensor readings for context
        recent_values = self._get_recent_values(
            anomaly_event.plot,
            sensor_type,
            hours=6
        )
        
        # Create rule context
        context = RuleContext(
            anomaly_type=anomaly_event.anomaly_type,
            severity=anomaly_event.severity,
            model_confidence=anomaly_event.model_confidence,
            sensor_type=sensor_type,
            plot_id=anomaly_event.plot.id,
            recent_values=recent_values,
            timestamp=anomaly_event.timestamp
        )
        
        # Evaluate rules
        recommendation = self.rule_engine.evaluate(context)
        
        # Generate explanation
        anomaly_dict = {
            'timestamp': anomaly_event.timestamp,
            'anomaly_type': anomaly_event.anomaly_type,
            'severity': anomaly_event.severity,
            'model_confidence': anomaly_event.model_confidence
        }
        
        explanation = self.explanation_generator.generate_explanation(
            anomaly_dict,
            recommendation
        )
        
        return {
            'action': recommendation.get('action'),
            'explanation': explanation,
            'confidence': recommendation.get('confidence'),
            'urgency': recommendation.get('urgency'),
            'details': recommendation.get('details', {})
        }
    
    def _extract_sensor_type(self, anomaly_type: str) -> str:
        """Extract sensor type from anomaly type string."""
        anomaly_lower = anomaly_type.lower()
        
        if 'moisture' in anomaly_lower or 'soil' in anomaly_lower:
            return 'moisture'
        elif 'temperature' in anomaly_lower or 'temp' in anomaly_lower:
            return 'temperature'
        elif 'humidity' in anomaly_lower:
            return 'humidity'
        else:
            return 'unknown'
    
    def _get_recent_values(
        self,
        plot,
        sensor_type: str,
        hours: int = 6
    ) -> List[float]:
        """Get recent sensor readings for the plot."""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        readings = SensorReading.objects.filter(
            plot=plot,
            timestamp__gte=cutoff_time
        ).order_by('timestamp')
        
        # Extract values based on sensor type
        values = []
        for reading in readings:
            if sensor_type == 'moisture' and reading.soil_moisture is not None:
                values.append(reading.soil_moisture)
            elif sensor_type == 'temperature' and reading.air_temperature is not None:
                values.append(reading.air_temperature)
            elif sensor_type == 'humidity' and reading.air_humidity is not None:
                values.append(reading.air_humidity)
        
        return values[-10:] if values else []  # Return last 10 values


class AgentRecommendationService:
    """
    High-level service for creating and managing agent recommendations.
    """
    
    def __init__(self):
        self.decision_engine = AgentDecisionEngine()
    
    def create_recommendation_for_anomaly(
        self,
        anomaly_event: AnomalyEvent
    ) -> Optional[AgentRecommendation]:
        """
        Create a recommendation for an anomaly event.
        
        Args:
            anomaly_event: The anomaly to process
            
        Returns:
            Created AgentRecommendation or None
        """
        try:
            # Check if recommendation already exists
            if hasattr(anomaly_event, 'recommendation'):
                return anomaly_event.recommendation
            
            # Process anomaly
            result = self.decision_engine.process_anomaly(anomaly_event)
            
            # Create recommendation
            recommendation = AgentRecommendation.objects.create(
                anomaly_event=anomaly_event,
                recommended_action=result['action'],
                explanation_text=result['explanation'],
                confidence=result['confidence']
            )
            
            return recommendation
        
        except Exception as e:
            print(f"Error creating recommendation: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def batch_process_unprocessed_anomalies(self) -> Dict:
        """
        Process all anomalies that don't have recommendations yet.
        
        Returns:
            Statistics about the batch processing
        """
        # Find anomalies without recommendations
        unprocessed = AnomalyEvent.objects.filter(
            recommendation__isnull=True
        ).order_by('timestamp')
        
        total = unprocessed.count()
        processed = 0
        failed = 0
        errors = []
        
        for anomaly in unprocessed:
            try:
                recommendation = self.create_recommendation_for_anomaly(anomaly)
                if recommendation:
                    processed += 1
                else:
                    failed += 1
                    errors.append({
                        'anomaly_id': anomaly.id,
                        'error': 'Failed to create recommendation'
                    })
            except Exception as e:
                failed += 1
                errors.append({
                    'anomaly_id': anomaly.id,
                    'error': str(e)
                })
        
        return {
            'total_unprocessed': total,
            'processed': processed,
            'failed': failed,
            'errors': errors
        }
    
    def get_recommendations_for_plot(
        self,
        plot_id: int,
        days: int = 7
    ) -> List[AgentRecommendation]:
        """
        Get recommendations for a specific plot.
        
        Args:
            plot_id: ID of the plot
            days: Number of days to look back
            
        Returns:
            List of recommendations
        """
        cutoff_time = timezone.now() - timedelta(days=days)
        
        return AgentRecommendation.objects.filter(
            anomaly_event__plot_id=plot_id,
            timestamp__gte=cutoff_time
        ).select_related('anomaly_event', 'anomaly_event__plot').order_by('-timestamp')