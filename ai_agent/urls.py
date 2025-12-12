"""
AI Agent URL Configuration
"""

from django.urls import path
from . import views

app_name = 'ai_agent'

urlpatterns = [
    # Process anomalies
    path('process/<int:anomaly_id>/', views.process_single_anomaly, name='process_single'),
    path('process-pending/', views.process_pending_anomalies, name='process_pending'),
    
    # Get recommendations
    path('recommendations/', views.get_recommendations, name='recommendations_list'),
    path('recommendations/<int:recommendation_id>/', views.get_recommendation_detail, name='recommendation_detail'),
    
    # Agent status
    path('status/', views.agent_status, name='agent_status'),
]