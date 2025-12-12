"""
AI Agent Service
Orchestrates the rule engine and creates recommendations.
"""

from crop_app.models import AnomalyEvent, AgentRecommendation
from .rule_engine import AgriculturalRuleEngine
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class AgentService:
    """
    Service layer for AI Agent operations.
    Processes anomaly events and generates recommendations.
    """
    
    def __init__(self):
        self.rule_engine = AgriculturalRuleEngine()
    
    def process_anomaly(self, anomaly_event: AnomalyEvent) -> AgentRecommendation:
        """
        Process a single anomaly event and create a recommendation.
        
        Args:
            anomaly_event: The AnomalyEvent to process
            
        Returns:
            AgentRecommendation instance
        """
        try:
            # Check if recommendation already exists
            if hasattr(anomaly_event, 'recommendation'):
                logger.info(f"Recommendation already exists for anomaly {anomaly_event.id}")
                return anomaly_event.recommendation
            
            # Analyze the anomaly using rule engine
            analysis = self.rule_engine.analyze_anomaly(anomaly_event)
            
            # Create recommendation record
            with transaction.atomic():
                recommendation = AgentRecommendation.objects.create(
                    anomaly_event=anomaly_event,
                    recommended_action=analysis['recommended_action'],
                    explanation_text=analysis['explanation_text'],
                    confidence=analysis['confidence']
                )
            
            logger.info(
                f"✅ Created recommendation {recommendation.id} for anomaly {anomaly_event.id} "
                f"(confidence: {recommendation.confidence:.2f})"
            )
            
            return recommendation
        
        except Exception as e:
            logger.error(f"❌ Error processing anomaly {anomaly_event.id}: {e}")
            raise
    
    def process_multiple_anomalies(self, anomaly_events: list) -> list:
        """
        Process multiple anomaly events.
        
        Args:
            anomaly_events: List of AnomalyEvent instances
            
        Returns:
            List of created AgentRecommendation instances
        """
        recommendations = []
        
        for anomaly in anomaly_events:
            try:
                rec = self.process_anomaly(anomaly)
                recommendations.append(rec)
            except Exception as e:
                logger.error(f"Failed to process anomaly {anomaly.id}: {e}")
                continue
        
        return recommendations
    
    def get_pending_anomalies(self, plot_id=None):
        """
        Get anomalies that don't have recommendations yet.
        
        Args:
            plot_id: Optional plot filter
            
        Returns:
            QuerySet of AnomalyEvent instances
        """
        query = AnomalyEvent.objects.filter(recommendation__isnull=True)
        
        if plot_id:
            query = query.filter(plot_id=plot_id)
        
        return query.order_by('-timestamp')
    
    def process_pending_anomalies(self, plot_id=None):
        """
        Process all pending anomalies (no recommendation yet).
        
        Args:
            plot_id: Optional plot filter
            
        Returns:
            Dict with results summary
        """
        pending = self.get_pending_anomalies(plot_id)
        count = pending.count()
        
        if count == 0:
            return {
                'success': True,
                'processed': 0,
                'message': 'No pending anomalies'
            }
        
        logger.info(f"Processing {count} pending anomalies...")
        
        recommendations = self.process_multiple_anomalies(list(pending))
        
        return {
            'success': True,
            'processed': len(recommendations),
            'total_pending': count,
            'failed': count - len(recommendations)
        }


# Singleton instance
_agent_service = None

def get_agent_service() -> AgentService:
    """Get or create the singleton agent service instance."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service