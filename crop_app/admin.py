
from django.contrib import admin
from .models import FarmProfile, FieldPlot, SensorReading, AnomalyEvent, AgentRecommendation


@admin.register(FarmProfile)
class FarmProfileAdmin(admin.ModelAdmin):
    """Admin interface for FarmProfile"""
    list_display = ['id', 'owner', 'location', 'size', 'crop_type', 'created_at']
    list_filter = ['crop_type', 'created_at']
    search_fields = ['location', 'owner__username', 'owner__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Owner Information', {
            'fields': ('owner',)
        }),
        ('Farm Details', {
            'fields': ('location', 'size', 'crop_type')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FieldPlot)
class FieldPlotAdmin(admin.ModelAdmin):
    """Admin interface for FieldPlot"""
    list_display = ['id', 'plot_name', 'farm', 'crop_variety', 'created_at']
    list_filter = ['crop_variety', 'created_at']
    search_fields = ['plot_name', 'farm__owner__username']
    readonly_fields = ['created_at']


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    """Admin interface for SensorReading"""
    list_display = ['id', 'plot', 'sensor_type', 'value', 'timestamp', 'source']
    list_filter = ['sensor_type', 'source', 'timestamp']
    search_fields = ['plot__plot_name', 'plot__farm__owner__username']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    # Show only recent readings by default
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('plot__farm__owner')


@admin.register(AnomalyEvent)
class AnomalyEventAdmin(admin.ModelAdmin):
    """Admin interface for AnomalyEvent"""
    list_display = ['id', 'plot', 'anomaly_type', 'severity', 
                    'model_confidence', 'timestamp']
    list_filter = ['anomaly_type', 'severity', 'timestamp']
    search_fields = ['plot__plot_name', 'anomaly_type']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


@admin.register(AgentRecommendation)
class AgentRecommendationAdmin(admin.ModelAdmin):
    """Admin interface for AgentRecommendation"""
    list_display = ['id', 'anomaly_event', 'recommended_action', 
                    'confidence', 'timestamp']
    list_filter = ['confidence', 'timestamp']
    search_fields = ['recommended_action', 'explanation_text']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Anomaly Link', {
            'fields': ('anomaly_event',)
        }),
        ('Recommendation', {
            'fields': ('recommended_action', 'explanation_text', 'confidence')
        }),
        ('Timestamp', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )