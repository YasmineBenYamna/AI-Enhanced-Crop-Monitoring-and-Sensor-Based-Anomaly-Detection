"""
AI Agent - Explanation Generator
Template-based explanation system for agent recommendations.
Generates human-readable, actionable explanations.
"""

from typing import Dict
from datetime import datetime


class ExplanationGenerator:
    """
    Generates human-readable explanations for agent recommendations.
    Uses deterministic template-based approach (no LLM required).
    """
    
    @staticmethod
    def generate_explanation(
        anomaly_event: Dict,
        recommendation: Dict,
        sensor_context: Dict = None
    ) -> str:
        """
        Generate complete explanation for a recommendation.
        
        Args:
            anomaly_event: AnomalyEvent data
            recommendation: Recommendation from rule engine
            sensor_context: Optional sensor reading context
        
        Returns:
            Formatted explanation text
        """
        timestamp = anomaly_event.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        anomaly_type = anomaly_event.get('anomaly_type', 'unknown')
        severity = anomaly_event.get('severity', 'unknown')
        confidence = anomaly_event.get('model_confidence', 0.0)
        
        # Build explanation components
        time_str = ExplanationGenerator._format_timestamp(timestamp)
        detection_str = ExplanationGenerator._format_detection(
            anomaly_type, severity, confidence
        )
        context_str = ExplanationGenerator._format_context(
            recommendation, sensor_context
        )
        action_str = ExplanationGenerator._format_action(recommendation)
        confidence_str = ExplanationGenerator._format_confidence(
            recommendation['confidence']
        )
        
        # Combine into full explanation
        explanation = (
            f"{time_str}, {detection_str}. "
            f"{context_str} "
            f"{action_str} "
            f"{confidence_str}"
        )
        
        return explanation.strip()
    
    @staticmethod
    def _format_timestamp(timestamp: datetime) -> str:
        """Format timestamp for explanation."""
        return f"On {timestamp.strftime('%Y-%m-%d at %H:%M')}"
    
    @staticmethod
    def _format_detection(
        anomaly_type: str,
        severity: str,
        confidence: float
    ) -> str:
        """Format detection information."""
        # Extract sensor type from anomaly_type
        sensor = 'sensor'
        if 'moisture' in anomaly_type.lower():
            sensor = 'soil moisture'
        elif 'temperature' in anomaly_type.lower():
            sensor = 'temperature'
        elif 'humidity' in anomaly_type.lower():
            sensor = 'humidity'
        
        severity_desc = severity.lower() if severity != 'CRITICAL' else 'critical'
        
        return (
            f"sensor readings detected a {severity_desc} {sensor} anomaly "
            f"(model confidence: {confidence:.2f})"
        )
    
    @staticmethod
    def _format_context(
        recommendation: Dict,
        sensor_context: Dict = None
    ) -> str:
        """Format contextual information."""
        reasoning = recommendation.get('reasoning', '')
        details = recommendation.get('details', {})
        
        context_parts = []
        
        # Add reasoning
        if reasoning:
            context_parts.append(reasoning)
        
        # Add specific details based on type
        if 'drop_percentage' in details:
            drop = details['drop_percentage']
            context_parts.append(
                f"Soil moisture decreased {drop:.1f}% in recent readings"
            )
        
        if 'current_humidity' in details:
            humidity = details['current_humidity']
            if humidity > 85:
                context_parts.append(
                    f"Current humidity level of {humidity:.1f}% is in disease risk range"
                )
            elif humidity < 30:
                context_parts.append(
                    f"Current humidity level of {humidity:.1f}% may stress crops"
                )
        
        if 'current_reading' in details and 'previous_reading' in details:
            current = details['current_reading']
            previous = details['previous_reading']
            change = abs(current - previous)
            context_parts.append(
                f"Reading changed from {previous:.1f} to {current:.1f} "
                f"(change: {change:.1f})"
            )
        
        return '. '.join(context_parts) + '.' if context_parts else ''
    
    @staticmethod
    def _format_action(recommendation: Dict) -> str:
        """Format recommended action."""
        action = recommendation.get('action', 'general_monitoring')
        description = recommendation.get('description', '')
        urgency = recommendation.get('urgency', 'medium')
        
        # Urgency prefix
        urgency_prefix = ""
        if urgency == 'high':
            urgency_prefix = "Immediate action required: "
        elif urgency == 'medium':
            urgency_prefix = "Recommended action: "
        else:
            urgency_prefix = "Suggested action: "
        
        return f"{urgency_prefix}{description}."
    
    @staticmethod
    def _format_confidence(confidence: float) -> str:
        """Format confidence level."""
        if confidence >= 0.8:
            level = "high"
        elif confidence >= 0.6:
            level = "moderate"
        else:
            level = "low"
        
        return f"Agent confidence: {level} ({confidence:.2f})."
    
    @staticmethod
    def generate_summary(recommendation: Dict) -> str:
        """
        Generate a short summary (for notifications/alerts).
        
        Args:
            recommendation: Recommendation from rule engine
        
        Returns:
            Brief summary text
        """
        description = recommendation.get('description', 'Action required')
        urgency = recommendation.get('urgency', 'medium')
        
        urgency_emoji = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }
        
        emoji = urgency_emoji.get(urgency, '⚠️')
        
        return f"{emoji} {description}"
    
    @staticmethod
    def generate_action_list(recommendation: Dict) -> str:
        """
        Generate formatted action list from recommendation details.
        
        Args:
            recommendation: Recommendation with details
        
        Returns:
            Formatted action list as string
        """
        details = recommendation.get('details', {})
        actions = details.get('recommended_actions', [])
        
        if not actions:
            return "No specific actions listed."
        
        # Format as numbered list
        action_text = "Recommended steps:\n"
        for i, action in enumerate(actions, 1):
            action_text += f"{i}. {action}\n"
        
        return action_text.strip()


class ExplanationTemplates:
    """
    Pre-defined explanation templates for common scenarios.
    Can be used for quick generation or customization.
    """
    
    TEMPLATES = {
        'irrigation_failure': (
            "On {timestamp}, sensor readings detected a {severity} soil moisture anomaly "
            "(model confidence: {confidence:.2f}). Soil moisture decreased {drop}% rapidly. "
            "Immediate action required: Check irrigation system immediately - possible leak or pump failure. "
            "Agent confidence: high."
        ),
        
        'heat_stress': (
            "On {timestamp}, sensor readings detected a {severity} temperature anomaly "
            "(model confidence: {confidence:.2f}). Critical temperature levels detected. "
            "Immediate action required: Apply heat stress mitigation - increase irrigation and consider shade. "
            "Agent confidence: high."
        ),
        
        'humidity_disease_risk': (
            "On {timestamp}, sensor readings detected a {severity} humidity anomaly "
            "(model confidence: {confidence:.2f}). Current humidity level of {humidity}% is in disease risk range. "
            "Recommended action: Monitor for fungal diseases and improve air circulation. "
            "Agent confidence: moderate."
        ),
        
        'sensor_malfunction': (
            "On {timestamp}, sensor readings detected unusual patterns "
            "(model confidence: {confidence:.2f}). {reason} "
            "Recommended action: Check sensor functionality - possible malfunction detected. "
            "Agent confidence: high."
        ),
        
        'low_confidence': (
            "On {timestamp}, sensor readings detected a {severity} anomaly "
            "(model confidence: {confidence:.2f}). Low model confidence - verification needed. "
            "Suggested action: Monitor closely and verify with manual inspection. "
            "Agent confidence: low."
        ),
        
        'multiple_anomaly': (
            "On {timestamp}, multiple sensor anomalies detected across {sensors}. "
            "Multiple stress factors identified. "
            "Immediate action required: Comprehensive plot inspection required. "
            "Agent confidence: high."
        )
    }
    
    @classmethod
    def get_template(cls, rule_name: str) -> str:
        """Get template for specific rule."""
        return cls.TEMPLATES.get(rule_name, cls.TEMPLATES['low_confidence'])


# Example usage
if __name__ == '__main__':
    print("Testing Explanation Generator...\n")
    
    generator = ExplanationGenerator()
    
    # Test Case 1: Irrigation failure
    print("Test 1: Irrigation Failure Explanation")
    anomaly1 = {
        'timestamp': datetime.now(),
        'anomaly_type': 'moisture_anomaly',
        'severity': 'HIGH',
        'model_confidence': 0.85
    }
    recommendation1 = {
        'action': 'immediate_irrigation_check',
        'description': 'Check irrigation system immediately - possible leak or pump failure',
        'urgency': 'high',
        'confidence': 0.95,
        'reasoning': 'Soil moisture dropped 15.2% rapidly',
        'details': {
            'drop_percentage': 15.2,
            'initial_value': 65.0,
            'current_value': 55.0
        }
    }
    
    explanation1 = generator.generate_explanation(anomaly1, recommendation1)
    print(explanation1)
    print()
    
    # Test Case 2: Heat stress
    print("Test 2: Heat Stress Explanation")
    anomaly2 = {
        'timestamp': datetime.now(),
        'anomaly_type': 'temperature_anomaly',
        'severity': 'CRITICAL',
        'model_confidence': 0.92
    }
    recommendation2 = {
        'action': 'heat_stress_mitigation',
        'description': 'Apply heat stress mitigation - increase irrigation and consider shade',
        'urgency': 'high',
        'confidence': 0.92,
        'reasoning': 'Critical temperature levels detected',
        'details': {
            'recommended_actions': [
                'Increase irrigation frequency',
                'Deploy shade structures if available'
            ]
        }
    }
    
    explanation2 = generator.generate_explanation(anomaly2, recommendation2)
    print(explanation2)
    print()
    
    # Test Case 3: Summary generation
    print("Test 3: Summary Generation")
    summary = generator.generate_summary(recommendation1)
    print(summary)
    print()
    
    # Test Case 4: Action list
    print("Test 4: Action List")
    action_list = generator.generate_action_list(recommendation2)
    print(action_list)
    
    print("\n✅ Explanation Generator tests completed!")