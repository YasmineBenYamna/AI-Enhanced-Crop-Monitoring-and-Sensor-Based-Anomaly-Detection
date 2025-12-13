"""
AI Agent - Django Signals
Automatically trigger agent recommendations when anomalies are detected.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from crop_app.models import AnomalyEvent, AgentRecommendation


@receiver(post_save, sender=AnomalyEvent)
def create_agent_recommendation(sender, instance, created, **kwargs):
    """
    Signal handler: Create agent recommendation when anomaly is detected.
    """
    if not created:
        return
    
    if hasattr(instance, 'recommendation'):
        return
    
    try:
        # Import INSIDE the function to avoid import errors at startup
        from .agent_service import AgentRecommendationService
        
        service = AgentRecommendationService()
        recommendation = service.create_recommendation_for_anomaly(instance)
        
        if recommendation:
            print(f"✅ Signal: Created recommendation for anomaly {instance.id}")
        else:
            print(f"⚠️ Signal: Failed to create recommendation for anomaly {instance.id}")
    
    except ImportError as e:
        print(f"⚠️ AgentRecommendationService not available yet: {e}")
    except Exception as e:
        print(f"❌ Signal error for anomaly {instance.id}: {e}")
        import traceback
        traceback.print_exc()


def process_unprocessed_anomalies_signal():
    """
    Utility function to batch process anomalies without recommendations.
    """
    try:
        from .agent_service import AgentRecommendationService
        
        service = AgentRecommendationService()
        stats = service.batch_process_unprocessed_anomalies()
        
        print(f"Batch processing completed:")
        print(f"  Total unprocessed: {stats['total_unprocessed']}")
        print(f"  Successfully processed: {stats['processed']}")
        print(f"  Failed: {stats['failed']}")
        
        if stats['errors']:
            print("  Errors:")
            for error in stats['errors']:
                print(f"    Anomaly {error['anomaly_id']}: {error['error']}")
        
        return stats
    except ImportError as e:
        print(f"⚠️ AgentRecommendationService not available: {e}")
        return {'error': 'Service not available'}