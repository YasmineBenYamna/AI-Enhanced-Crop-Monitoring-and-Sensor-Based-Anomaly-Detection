"""
Django Signals for AI Agent
Automatically trigger agent when anomalies are created.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from crop_app.models import AnomalyEvent
from .agent_service import get_agent_service
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=AnomalyEvent)
def process_anomaly_event(sender, instance, created, **kwargs):
    """
    Signal handler: When an AnomalyEvent is created,
    automatically generate a recommendation.
    
    Args:
        sender: The model class (AnomalyEvent)
        instance: The actual AnomalyEvent instance
        created: Boolean - True if this is a new record
        **kwargs: Additional keyword arguments
    """
    if created:  # Only process new anomalies
        logger.info(f"🚨 New anomaly detected: {instance.id} - {instance.anomaly_type}")
        
        try:
            agent_service = get_agent_service()
            recommendation = agent_service.process_anomaly(instance)
            
            logger.info(
                f"✅ Agent recommendation created: {recommendation.recommended_action}"
            )
        except Exception as e:
            logger.error(f"❌ Failed to create recommendation for anomaly {instance.id}: {e}")