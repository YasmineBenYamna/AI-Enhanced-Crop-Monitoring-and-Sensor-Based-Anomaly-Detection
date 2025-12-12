"""
AI Agent App Configuration
Registers signals on app startup.
"""

from django.apps import AppConfig


class AiAgentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_agent'
    verbose_name = 'AI Agent Module'
    
    def ready(self):
        """Import signals when app is ready."""
        import ai_agent.signals  # This registers the signal handlers
