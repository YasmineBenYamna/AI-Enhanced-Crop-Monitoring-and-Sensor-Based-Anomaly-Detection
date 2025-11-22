from django.contrib import admin
from .models import FarmProfile, FieldPlot, SensorReading, AnomalyEvent, AgentRecommendation


@admin.register(FarmProfile)
class FarmProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'owner', 'location', 'crop_type', 'size', 'created_at']
    list_filter = ['crop_type', 'location']
    search_fields = ['owner', 'location', 'crop_type']
    ordering = ['owner']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FieldPlot)
class FieldPlotAdmin(admin.ModelAdmin):
    list_display = ['id', 'plot_name', 'crop_variety', 'farm', 'created_at']
    list_filter = ['crop_variety', 'farm']
    search_fields = ['plot_name', 'crop_variety', 'farm__owner']
    ordering = ['id']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        """Optimize queries by selecting related farm"""
        qs = super().get_queryset(request)
        return qs.select_related('farm')


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ['id', 'timestamp', 'plot', 'sensor_type', 'value', 'source']
    list_filter = ['sensor_type', 'source', 'timestamp']
    search_fields = ['plot__plot_name', 'plot__farm__owner']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'

    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('plot__farm')


@admin.register(AnomalyEvent)
class AnomalyEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'timestamp', 'plot', 'anomaly_type', 'severity', 'model_confidence', 'has_recommendation']
    list_filter = ['severity', 'anomaly_type', 'timestamp']
    search_fields = ['anomaly_type', 'plot__plot_name', 'plot__farm__owner']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'

    def has_recommendation(self, obj):
        """Show if anomaly has a recommendation"""
        try:
            return obj.recommendation is not None
        except AgentRecommendation.DoesNotExist:
            return False
    has_recommendation.boolean = True
    has_recommendation.short_description = 'Has Recommendation'

    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('plot__farm').prefetch_related('recommendation')


@admin.register(AgentRecommendation)
class AgentRecommendationAdmin(admin.ModelAdmin):
    list_display = ['id', 'timestamp', 'anomaly_event', 'recommended_action', 'confidence']
    list_filter = ['confidence', 'timestamp']
    search_fields = ['recommended_action', 'explanation_text', 'anomaly_event__anomaly_type']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'

    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('anomaly_event__plot__farm')