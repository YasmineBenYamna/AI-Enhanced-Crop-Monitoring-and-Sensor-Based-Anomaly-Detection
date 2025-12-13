"""
AI Agent - Rule Engine
Rule-based decision system for agricultural anomaly response.
Implements domain-specific heuristics for crop monitoring.
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class RuleContext:
    """Context information for rule evaluation."""
    anomaly_type: str
    severity: str
    model_confidence: float
    sensor_type: str
    plot_id: int
    recent_values: List[float] = None
    timestamp: datetime = None


class AgriculturalRule:
    """Base class for agricultural decision rules."""
    
    def __init__(self, name: str, priority: int = 5):
        """
        Initialize rule.
        
        Args:
            name: Rule identifier
            priority: Rule priority (1-10, higher = more important)
        """
        self.name = name
        self.priority = priority
    
    def evaluate(self, context: RuleContext) -> Optional[Dict]:
        """
        Evaluate if rule applies to context.
        
        Args:
            context: Current anomaly context
        
        Returns:
            Recommendation dict if rule applies, None otherwise
        """
        raise NotImplementedError("Subclasses must implement evaluate()")


class IrrigationFailureRule(AgriculturalRule):
    """Detects irrigation system failures from moisture drops."""
    
    def __init__(self):
        super().__init__("irrigation_failure", priority=9)
    
    def evaluate(self, context: RuleContext) -> Optional[Dict]:
        """
        Rule: Rapid moisture drop indicates irrigation failure.
        
        Triggers when:
        - Sensor type is moisture
        - Severe anomaly detected
        - Sudden drop pattern
        """
        if context.sensor_type != 'moisture':
            return None
        
        if context.severity not in ['HIGH', 'CRITICAL']:
            return None
        
        # Check for rapid drop pattern
        if context.recent_values and len(context.recent_values) >= 3:
            # Calculate drop percentage
            initial = context.recent_values[0]
            current = context.recent_values[-1]
            drop_percentage = ((initial - current) / initial) * 100 if initial > 0 else 0
            
            if drop_percentage > 10:  # More than 10% drop
                return {
                    'action': 'immediate_irrigation_check',
                    'description': 'Check irrigation system immediately - possible leak or pump failure',
                    'urgency': 'high',
                    'confidence': min(0.95, context.model_confidence + 0.1),
                    'reasoning': f'Soil moisture dropped {drop_percentage:.1f}% rapidly',
                    'details': {
                        'drop_percentage': drop_percentage,
                        'initial_value': initial,
                        'current_value': current,
                        'time_window': 'recent readings'
                    }
                }
        
        # General moisture anomaly
        return {
            'action': 'irrigation_check',
            'description': 'Inspect irrigation system and verify water supply',
            'urgency': 'medium',
            'confidence': context.model_confidence,
            'reasoning': 'Abnormal moisture levels detected',
            'details': {}
        }


class HeatStressRule(AgriculturalRule):
    """Detects heat stress conditions from temperature anomalies."""
    
    def __init__(self):
        super().__init__("heat_stress", priority=8)
    
    def evaluate(self, context: RuleContext) -> Optional[Dict]:
        """
        Rule: High temperature anomalies indicate heat stress.
        
        Triggers when:
        - Sensor type is temperature
        - Sustained high temperatures
        """
        if context.sensor_type != 'temperature':
            return None
        
        if context.severity == 'CRITICAL':
            return {
                'action': 'heat_stress_mitigation',
                'description': 'Apply heat stress mitigation - increase irrigation and consider shade',
                'urgency': 'high',
                'confidence': context.model_confidence,
                'reasoning': 'Critical temperature levels detected',
                'details': {
                    'recommended_actions': [
                        'Increase irrigation frequency',
                        'Deploy shade structures if available',
                        'Monitor crop for wilting',
                        'Consider early morning watering'
                    ]
                }
            }
        
        elif context.severity in ['HIGH', 'MEDIUM']:
            return {
                'action': 'temperature_monitoring',
                'description': 'Monitor temperature closely and prepare heat mitigation measures',
                'urgency': 'medium',
                'confidence': context.model_confidence,
                'reasoning': 'Elevated temperature levels detected',
                'details': {
                    'recommended_actions': [
                        'Monitor temperature trends',
                        'Prepare irrigation system',
                        'Check soil moisture levels'
                    ]
                }
            }
        
        return None


class HumidityAnomalyRule(AgriculturalRule):
    """Detects humidity-related issues."""
    
    def __init__(self):
        super().__init__("humidity_anomaly", priority=7)
    
    def evaluate(self, context: RuleContext) -> Optional[Dict]:
        """
        Rule: Humidity anomalies can indicate disease risk or stress.
        
        Triggers when:
        - Sensor type is humidity
        - Abnormal humidity levels
        """
        if context.sensor_type != 'humidity':
            return None
        
        if context.recent_values and len(context.recent_values) > 0:
            current_humidity = context.recent_values[-1]
            
            # Very high humidity = disease risk
            if current_humidity > 85:
                return {
                    'action': 'disease_prevention',
                    'description': 'High humidity detected - monitor for fungal diseases',
                    'urgency': 'medium',
                    'confidence': context.model_confidence,
                    'reasoning': f'Humidity at {current_humidity:.1f}% increases disease risk',
                    'details': {
                        'current_humidity': current_humidity,
                        'risk_factors': ['Fungal diseases', 'Bacterial infections'],
                        'recommended_actions': [
                            'Improve air circulation',
                            'Inspect crops for disease symptoms',
                            'Consider preventive fungicide application'
                        ]
                    }
                }
            
            # Very low humidity = stress
            elif current_humidity < 30:
                return {
                    'action': 'humidity_management',
                    'description': 'Low humidity detected - crops may experience stress',
                    'urgency': 'medium',
                    'confidence': context.model_confidence,
                    'reasoning': f'Humidity at {current_humidity:.1f}% may cause crop stress',
                    'details': {
                        'current_humidity': current_humidity,
                        'recommended_actions': [
                            'Increase irrigation frequency',
                            'Monitor crop for wilting',
                            'Consider mulching to retain moisture'
                        ]
                    }
                }
        
        # General humidity anomaly
        return {
            'action': 'humidity_monitoring',
            'description': 'Monitor humidity levels and adjust management practices',
            'urgency': 'low',
            'confidence': context.model_confidence,
            'reasoning': 'Abnormal humidity patterns detected',
            'details': {}
        }


class MultipleAnomalyRule(AgriculturalRule):
    """Detects multiple simultaneous anomalies indicating complex issues."""
    
    def __init__(self):
        super().__init__("multiple_anomaly", priority=10)
    
    def evaluate(self, context: RuleContext) -> Optional[Dict]:
        """
        Rule: Multiple anomalies require comprehensive investigation.
        
        Note: This rule is triggered by the agent when multiple
        anomaly types are detected for the same plot.
        """
        # This rule is evaluated differently - see AgentDecisionEngine
        return None


class LowConfidenceRule(AgriculturalRule):
    """Handles low-confidence anomaly detections."""
    
    def __init__(self):
        super().__init__("low_confidence", priority=3)
    
    def evaluate(self, context: RuleContext) -> Optional[Dict]:
        """
        Rule: Low confidence detections need manual verification.
        
        Triggers when:
        - Model confidence is low (0.4-0.6)
        """
        if 0.4 <= context.model_confidence <= 0.6:
            return {
                'action': 'manual_inspection',
                'description': 'Monitor closely and verify with manual inspection',
                'urgency': 'low',
                'confidence': context.model_confidence,
                'reasoning': 'Low model confidence - verification needed',
                'details': {
                    'model_confidence': context.model_confidence,
                    'recommended_actions': [
                        'Manual visual inspection of plot',
                        'Verify sensor readings',
                        'Check sensor calibration',
                        'Monitor for pattern development'
                    ]
                }
            }
        
        return None


class SensorMalfunctionRule(AgriculturalRule):
    """Detects potential sensor malfunctions."""
    
    def __init__(self):
        super().__init__("sensor_malfunction", priority=6)
    
    def evaluate(self, context: RuleContext) -> Optional[Dict]:
        """
        Rule: Extreme or impossible values suggest sensor issues.
        
        Triggers when:
        - Values are outside physically possible ranges
        - Sudden spikes or impossible changes
        """
        if not context.recent_values or len(context.recent_values) < 2:
            return None
        
        current = context.recent_values[-1]
        previous = context.recent_values[-2]
        
        # Check for impossible values
        impossible = False
        reason = ""
        
        if context.sensor_type == 'moisture':
            if current < 0 or current > 100:
                impossible = True
                reason = f"Moisture reading {current}% is outside valid range (0-100%)"
        
        elif context.sensor_type == 'temperature':
            if current < -20 or current > 60:
                impossible = True
                reason = f"Temperature reading {current}°C is outside expected range"
        
        elif context.sensor_type == 'humidity':
            if current < 0 or current > 100:
                impossible = True
                reason = f"Humidity reading {current}% is outside valid range (0-100%)"
        
        # Check for impossible change rate
        if not impossible and abs(current - previous) > 50:
            impossible = True
            reason = f"Sudden change of {abs(current - previous):.1f} units is unlikely"
        
        if impossible:
            return {
                'action': 'sensor_check',
                'description': 'Check sensor functionality - possible malfunction detected',
                'urgency': 'high',
                'confidence': 0.8,
                'reasoning': reason,
                'details': {
                    'current_reading': current,
                    'previous_reading': previous,
                    'sensor_type': context.sensor_type,
                    'recommended_actions': [
                        'Inspect sensor physically',
                        'Check sensor connections',
                        'Verify sensor calibration',
                        'Consider sensor replacement if persistent'
                    ]
                }
            }
        
        return None


class RuleEngine:
    """
    Rule engine that evaluates multiple rules and selects best recommendation.
    """
    
    def __init__(self):
        """Initialize rule engine with all agricultural rules."""
        self.rules: List[AgriculturalRule] = [
            MultipleAnomalyRule(),
            IrrigationFailureRule(),
            HeatStressRule(),
            HumidityAnomalyRule(),
            SensorMalfunctionRule(),
            LowConfidenceRule(),
        ]
        
        # Sort by priority (highest first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def evaluate(self, context: RuleContext) -> Dict:
        """
        Evaluate all rules and return best recommendation.
        
        Args:
            context: Anomaly context for evaluation
        
        Returns:
            Best recommendation from applicable rules
        """
        recommendations = []
        
        # Evaluate all rules
        for rule in self.rules:
            try:
                recommendation = rule.evaluate(context)
                if recommendation:
                    recommendation['rule_name'] = rule.name
                    recommendation['rule_priority'] = rule.priority
                    recommendations.append(recommendation)
            except Exception as e:
                print(f"⚠️ Error in rule {rule.name}: {e}")
                continue
        
        # Select best recommendation (highest priority)
        if recommendations:
            best = max(recommendations, key=lambda r: r['rule_priority'])
            return best
        
        # Default recommendation if no rules triggered
        return {
            'action': 'general_monitoring',
            'description': 'Continue monitoring - anomaly detected but no specific action identified',
            'urgency': 'low',
            'confidence': context.model_confidence,
            'reasoning': 'Anomaly detected without specific classification',
            'rule_name': 'default',
            'rule_priority': 0,
            'details': {}
        }
    
    def evaluate_multiple_anomalies(self, contexts: List[RuleContext]) -> Dict:
        """
        Handle multiple simultaneous anomalies for same plot.
        
        Args:
            contexts: List of anomaly contexts for same plot
        
        Returns:
            Comprehensive recommendation
        """
        if len(contexts) == 1:
            return self.evaluate(contexts[0])
        
        # Multiple anomalies detected
        sensor_types = [c.sensor_type for c in contexts]
        avg_confidence = sum(c.model_confidence for c in contexts) / len(contexts)
        max_severity = max(contexts, key=lambda c: self._severity_score(c.severity)).severity
        
        return {
            'action': 'comprehensive_inspection',
            'description': 'Multiple anomalies detected - comprehensive plot inspection required',
            'urgency': 'high',
            'confidence': avg_confidence,
            'reasoning': f'Multiple sensor anomalies detected: {", ".join(set(sensor_types))}',
            'rule_name': 'multiple_anomaly',
            'rule_priority': 10,
            'details': {
                'affected_sensors': sensor_types,
                'max_severity': max_severity,
                'anomaly_count': len(contexts),
                'recommended_actions': [
                    'Comprehensive plot inspection',
                    'Check all sensor systems',
                    'Verify irrigation system',
                    'Assess crop health visually',
                    'Document all findings'
                ]
            }
        }
    
    def _severity_score(self, severity: str) -> int:
        """Convert severity to numeric score."""
        scores = {
            'CRITICAL': 4,
            'HIGH': 3,
            'MEDIUM': 2,
            'LOW': 1,
            'NORMAL': 0
        }
        return scores.get(severity, 0)


# Example usage
if __name__ == '__main__':
    print("Testing Rule Engine...\n")
    
    engine = RuleEngine()
    
    # Test Case 1: Irrigation failure
    print("Test 1: Irrigation Failure")
    context1 = RuleContext(
        anomaly_type='moisture_anomaly',
        severity='HIGH',
        model_confidence=0.85,
        sensor_type='moisture',
        plot_id=1,
        recent_values=[65.0, 60.0, 52.0, 45.0],
        timestamp=datetime.now()
    )
    result1 = engine.evaluate(context1)
    print(f"Action: {result1['action']}")
    print(f"Description: {result1['description']}")
    print(f"Confidence: {result1['confidence']:.2f}")
    print(f"Reasoning: {result1['reasoning']}\n")
    
    # Test Case 2: Heat stress
    print("Test 2: Heat Stress")
    context2 = RuleContext(
        anomaly_type='temperature_anomaly',
        severity='CRITICAL',
        model_confidence=0.92,
        sensor_type='temperature',
        plot_id=1,
        recent_values=[28.0, 32.0, 35.0, 38.0],
        timestamp=datetime.now()
    )
    result2 = engine.evaluate(context2)
    print(f"Action: {result2['action']}")
    print(f"Description: {result2['description']}")
    print(f"Urgency: {result2['urgency']}\n")
    
    # Test Case 3: Multiple anomalies
    print("Test 3: Multiple Anomalies")
    contexts = [context1, context2]
    result3 = engine.evaluate_multiple_anomalies(contexts)
    print(f"Action: {result3['action']}")
    print(f"Description: {result3['description']}")
    print(f"Affected sensors: {result3['details']['affected_sensors']}")
    print("\n✅ Rule Engine tests completed!")