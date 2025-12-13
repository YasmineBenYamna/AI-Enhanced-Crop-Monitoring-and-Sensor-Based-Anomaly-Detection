"""
AI Agent - Django Admin Configuration
Register models for admin interface.
"""

from django.contrib import admin
from crop_app.models import AgentRecommendation, AnomalyEvent


@admin.register(AgentRecommendation)
class AgentRecommendationAdmin(admin.ModelAdmin):
    """Admin interface for AgentRecommendation model."""
    
    list_display = [
        'id',
        'timestamp',
        'recommended_action',
        'confidence',
        'get_anomaly_type',
        'get_plot_name',
        'get_severity'
    ]
    
    list_filter = [
        'timestamp',
        'confidence',
        'anomaly_event__severity',
        'anomaly_event__anomaly_type'
    ]
    
    search_fields = [
        'recommended_action',
        'explanation_text',
        'anomaly_event__anomaly_type',
        'anomaly_event__plot__plot_name'
    ]
    
    readonly_fields = [
        'timestamp',
        'anomaly_event',
        'recommended_action',
        'explanation_text',
        'confidence'
    ]
    
    date_hierarchy = 'timestamp'
    
    ordering = ['-timestamp']
    
    def get_anomaly_type(self, obj):
        """Get anomaly type from related event."""
        return obj.anomaly_event.anomaly_type
    get_anomaly_type.short_description = 'Anomaly Type'
    
    def get_plot_name(self, obj):
        """Get plot name from related event."""
        return obj.anomaly_event.plot.plot_name or f"Plot {obj.anomaly_event.plot.id}"
    get_plot_name.short_description = 'Plot'
    
    def get_severity(self, obj):
        """Get severity from related event."""
        return obj.anomaly_event.severity
    get_severity.short_description = 'Severity'
    
    fieldsets = (
        ('Recommendation Info', {
            'fields': ('timestamp', 'confidence', 'recommended_action')
        }),
        ('Explanation', {
            'fields': ('explanation_text',),
            'classes': ('wide',)
        }),
        ('Related Anomaly', {
            'fields': ('anomaly_event',)
        }),
    )
    
    def has_add_permission(self, request):
        """Recommendations are created automatically by signals."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion for testing."""
        return True


# Optional: Also register AnomalyEvent if not already registered
# Uncomment if you want to view anomalies in admin
"""
@admin.register(AnomalyEvent)
class AnomalyEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'timestamp', 'anomaly_type', 'severity', 'model_confidence', 'plot']
    list_filter = ['severity', 'anomaly_type', 'timestamp']
    search_fields = ['anomaly_type', 'plot__plot_name']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
"""