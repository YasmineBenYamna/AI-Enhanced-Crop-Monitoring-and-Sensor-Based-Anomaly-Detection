"""
ML Module - URL Configuration
Routes for ML model training and anomaly detection endpoints.
"""

from django.urls import path
from . import views

app_name = 'ml_module'

urlpatterns = [
    # Train the anomaly detection model
    path('train/', views.train_model, name='train_model'),
    
    # Detect anomalies for a specific plot/sensor
    path('detect/', views.detect_anomalies, name='detect_anomalies'),
    
    # Get model training status
    path('status/', views.model_status, name='model_status'),
    
    # Batch detection for all plots
    path('batch-detect/', views.batch_detect, name='batch_detect'),
]


