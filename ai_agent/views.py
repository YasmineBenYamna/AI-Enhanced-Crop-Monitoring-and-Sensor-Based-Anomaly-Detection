from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from crop_app.models import AgentRecommendation, AnomalyEvent
from .serializers import AgentRecommendationSerializer
from .agent_service import AgentRecommendationService  # ✅ Correct


class AgentRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour consulter les recommandations de l'agent AI.
    """
    queryset = AgentRecommendation.objects.all().select_related(
        'anomaly_event', 
        'anomaly_event__plot',
        'anomaly_event__plot__farm'
    )
    serializer_class = AgentRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtre les recommandations selon l'utilisateur."""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Si pas admin, filtrer par fermes de l'utilisateur
        if not user.is_staff:
            queryset = queryset.filter(
                anomaly_event__plot__farm__owner=user
            )
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def by_plot(self, request):
        """
        Récupère les recommandations pour un plot spécifique.
        GET /api/agent/recommendations/by_plot/?plot_id=1
        """
        plot_id = request.query_params.get('plot_id')
        
        if not plot_id:
            return Response(
                {'error': 'plot_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ✅ Utiliser le bon nom de classe
        agent_service = AgentRecommendationService()
        recommendations = agent_service.get_recommendations_for_plot(plot_id)
        
        serializer = self.get_serializer(recommendations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def high_priority(self, request):
        """
        Récupère les recommandations haute priorité.
        GET /api/agent/recommendations/high_priority/
        """
        queryset = self.get_queryset()
        
        # Filtrer par haute priorité (confidence > 0.8)
        high_priority = queryset.filter(confidence__gte=0.8)
        
        farm_id = request.query_params.get('farm_id')
        if farm_id:
            high_priority = high_priority.filter(
                anomaly_event__plot__farm_id=farm_id
            )
        
        serializer = self.get_serializer(high_priority, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """
        Régénère une recommandation pour une anomalie donnée.
        POST /api/agent/recommendations/{id}/regenerate/
        """
        recommendation = self.get_object()
        anomaly_event = recommendation.anomaly_event
        
        # Supprimer l'ancienne recommandation
        recommendation.delete()
        
        # Générer une nouvelle recommandation
        agent_service = AgentRecommendationService()  # ✅ Correct
        new_recommendation = agent_service.create_recommendation_for_anomaly(anomaly_event)
        
        if new_recommendation:
            serializer = self.get_serializer(new_recommendation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'error': 'Failed to regenerate recommendation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )