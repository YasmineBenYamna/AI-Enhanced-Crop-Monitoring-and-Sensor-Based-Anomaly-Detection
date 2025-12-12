"""
AI Agent API Views
Endpoints for agent operations and recommendations.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from crop_app.models import AnomalyEvent, AgentRecommendation
from .agent_service import get_agent_service


@api_view(['POST'])
@permission_classes([AllowAny])
def process_single_anomaly(request, anomaly_id):
    """
    Manually trigger agent processing for a specific anomaly.
    
    POST /api/agent/process/<anomaly_id>/
    """
    anomaly = get_object_or_404(AnomalyEvent, id=anomaly_id)
    
    try:
        agent_service = get_agent_service()
        recommendation = agent_service.process_anomaly(anomaly)
        
        return Response({
            'success': True,
            'anomaly_id': anomaly.id,
            'recommendation': {
                'id': recommendation.id,
                'action': recommendation.recommended_action,
                'explanation': recommendation.explanation_text,
                'confidence': recommendation.confidence,
                'timestamp': recommendation.timestamp.isoformat()
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def process_pending_anomalies(request):
    """
    Process all anomalies that don't have recommendations yet.
    
    POST /api/agent/process-pending/
    Body (optional):
    {
        "plot_id": 1
    }
    """
    plot_id = request.data.get('plot_id')
    
    try:
        agent_service = get_agent_service()
        result = agent_service.process_pending_anomalies(plot_id)
        
        return Response(result, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_recommendations(request):
    """
    Get all recommendations with optional filtering.
    
    GET /api/agent/recommendations/?plot_id=1&limit=10
    """
    plot_id = request.GET.get('plot_id')
    limit = request.GET.get('limit', 50)
    
    try:
        limit = int(limit)
    except ValueError:
        limit = 50
    
    recommendations = AgentRecommendation.objects.select_related(
        'anomaly_event', 'anomaly_event__plot'
    ).order_by('-timestamp')
    
    if plot_id:
        recommendations = recommendations.filter(anomaly_event__plot_id=plot_id)
    
    recommendations = recommendations[:limit]
    
    data = []
    for rec in recommendations:
        data.append({
            'id': rec.id,
            'timestamp': rec.timestamp.isoformat(),
            'recommended_action': rec.recommended_action,
            'explanation_text': rec.explanation_text,
            'confidence': rec.confidence,
            'anomaly': {
                'id': rec.anomaly_event.id,
                'type': rec.anomaly_event.anomaly_type,
                'severity': rec.anomaly_event.severity,
                'plot_id': rec.anomaly_event.plot.id,
                'plot_name': rec.anomaly_event.plot.plot_name or f"Plot {rec.anomaly_event.plot.id}"
            }
        })
    
    return Response({
        'success': True,
        'count': len(data),
        'recommendations': data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_recommendation_detail(request, recommendation_id):
    """
    Get detailed information about a specific recommendation.
    
    GET /api/agent/recommendations/<id>/
    """
    recommendation = get_object_or_404(
        AgentRecommendation.objects.select_related(
            'anomaly_event',
            'anomaly_event__plot',
            'anomaly_event__sensor_reading'
        ),
        id=recommendation_id
    )
    
    anomaly = recommendation.anomaly_event
    
    data = {
        'id': recommendation.id,
        'timestamp': recommendation.timestamp.isoformat(),
        'recommended_action': recommendation.recommended_action,
        'explanation_text': recommendation.explanation_text,
        'confidence': recommendation.confidence,
        'anomaly': {
            'id': anomaly.id,
            'type': anomaly.anomaly_type,
            'severity': anomaly.severity,
            'model_confidence': anomaly.model_confidence,
            'timestamp': anomaly.timestamp.isoformat(),
            'plot': {
                'id': anomaly.plot.id,
                'name': anomaly.plot.plot_name or f"Plot {anomaly.plot.id}",
                'crop_variety': anomaly.plot.crop_variety
            }
        }
    }
    
    if anomaly.sensor_reading:
        data['anomaly']['sensor_reading'] = {
            'type': anomaly.sensor_reading.sensor_type,
            'value': anomaly.sensor_reading.value,
            'timestamp': anomaly.sensor_reading.timestamp.isoformat()
        }
    
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def agent_status(request):
    """
    Get agent status and statistics.
    
    GET /api/agent/status/
    """
    try:
        total_anomalies = AnomalyEvent.objects.count()
        total_recommendations = AgentRecommendation.objects.count()
        pending_anomalies = AnomalyEvent.objects.filter(recommendation__isnull=True).count()
        
        # Get recommendation confidence stats
        from django.db.models import Avg, Count
        confidence_stats = AgentRecommendation.objects.aggregate(
            avg_confidence=Avg('confidence'),
            count=Count('id')
        )
        
        # Get recommendations by priority (severity of linked anomaly)
        high_priority = AgentRecommendation.objects.filter(
            anomaly_event__severity='high'
        ).count()
        
        medium_priority = AgentRecommendation.objects.filter(
            anomaly_event__severity='medium'
        ).count()
        
        low_priority = AgentRecommendation.objects.filter(
            anomaly_event__severity='low'
        ).count()
        
        return Response({
            'success': True,
            'statistics': {
                'total_anomalies': total_anomalies,
                'total_recommendations': total_recommendations,
                'pending_anomalies': pending_anomalies,
                'coverage_rate': round(
                    (total_recommendations / total_anomalies * 100) if total_anomalies > 0 else 0,
                    2
                ),
                'average_confidence': round(
                    confidence_stats['avg_confidence'] or 0,
                    2
                ),
                'priority_distribution': {
                    'high': high_priority,
                    'medium': medium_priority,
                    'low': low_priority
                }
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)