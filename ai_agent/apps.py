"""
AI Agent - Django App Configuration
Registers signals and initializes the agent module.
"""

from django.apps import AppConfig


class AiAgentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_agent'
    verbose_name = 'AI Agent Module'
    
    def ready(self):
        """
        Initialize app when Django starts.
        This imports signals so they're registered.
        """
        # Import signals to register them
        import ai_agent.signals
        
        print("✅ AI Agent module initialized")
        print("   - Signals registered")
        print("   - Automatic recommendation generation enabled")