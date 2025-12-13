"""
AI Agent Module
Intelligent decision-making system for agricultural anomaly response.
"""

default_app_config = 'ai_agent.apps.AiAgentConfig'

__version__ = '1.0.0'
__author__ = 'Your Team'

# Don't import at module level - causes AppRegistryNotReady
# Import in your code when needed instead:
# from ai_agent.agent_service import AgentRecommendationService

__all__ = [
    'AgentDecisionEngine',
    'AgentRecommendationService',
    'RuleEngine',
    'RuleContext',
    'ExplanationGenerator',
]