from django.urls import path
from .views import (
    SensorReadingListCreate,
    AnomalyList,
    RecommendationList,
)
from django.urls import path
from . import views
urlpatterns = [
    # API endpoints
    path('sensor-readings/', SensorReadingListCreate.as_view(), name='sensor-readings'),
    path('anomalies/', AnomalyList.as_view(), name='anomalies'),
    path('recommendations/', RecommendationList.as_view(), name='recommendations'),
    path('', views.index, name='index'),
    path('index.html', views.index, name='index-html'),
    path('dashboard/', views.index, name='dashboard'),
    
    # Pages avec extension .html
    path('charts.html', views.charts, name='charts-html'),
    path('widgets.html', views.widgets, name='widgets-html'),
    path('colors.html', views.colors, name='colors-html'),
    path('typography.html', views.typography, name='typography-html'),
    path('login.html', views.login_page, name='login-html'),
    path('register.html', views.register, name='register-html'),
    path('404.html', views.error_404_page, name='404-html'),
    path('500.html', views.error_500_page, name='500-html'),
    path('charts/', views.charts, name='charts'),
    path('widgets/', views.widgets, name='widgets'),
    path('colors/', views.colors, name='colors'),
    path('typography/', views.typography, name='typography')
]