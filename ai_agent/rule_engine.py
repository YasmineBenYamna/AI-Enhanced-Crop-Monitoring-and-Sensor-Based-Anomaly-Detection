"""
AI Agent Rule Engine (Updated for your ML module)
Rule-based decision system for agricultural anomaly response.
"""

from typing import Dict, Tuple
from datetime import datetime, timedelta
from crop_app.models import AnomalyEvent, SensorReading


class AgriculturalRuleEngine:
    """
    Rule-based engine that analyzes anomaly events and determines
    appropriate actions based on agricultural domain knowledge.
    
    Works with your ML module's anomaly types:
    - moisture_anomaly
    - temperature_anomaly  
    - humidity_anomaly
    """
    
    def __init__(self):
        """Initialize the rule engine with agricultural thresholds."""
        # Define normal ranges for different sensors (from simulator config)
        self.normal_ranges = {
            'moisture': {'min': 45, 'max': 75},
            'temperature': {'min': 18, 'max': 28},
            'humidity': {'min': 45, 'max': 75}
        }
        
        # Define critical thresholds for immediate action
        self.critical_thresholds = {
            'moisture': {'critical_low': 35, 'critical_high': 80},
            'temperature': {'critical_low': 10, 'critical_high': 32},
            'humidity': {'critical_low': 30, 'critical_high': 85}
        }
    
    def analyze_anomaly(self, anomaly_event: AnomalyEvent) -> Dict:
        """
        Main analysis function that applies rules to an anomaly event.
        
        Args:
            anomaly_event: The AnomalyEvent instance to analyze
            
        Returns:
            Dict containing:
                - recommended_action: What to do
                - explanation_text: Why and what happened
                - confidence: How confident (0-1)
                - priority: low/medium/high
        """
        # Get recent sensor readings for context
        context = self._get_reading_context(anomaly_event)
        
        # Apply rules based on anomaly type (simpler approach)
        if 'moisture' in anomaly_event.anomaly_type.lower():
            result = self._analyze_moisture_anomaly(anomaly_event, context)
        elif 'temperature' in anomaly_event.anomaly_type.lower():
            result = self._analyze_temperature_anomaly(anomaly_event, context)
        elif 'humidity' in anomaly_event.anomaly_type.lower():
            result = self._analyze_humidity_anomaly(anomaly_event, context)
        else:
            result = self._analyze_generic_anomaly(anomaly_event, context)
        
        return result
    
    def _get_reading_context(self, anomaly_event: AnomalyEvent) -> Dict:
        """
        Get context about recent readings to help make better decisions.
        
        Returns:
            Dict with recent_value, change_rate, trend, historical_avg, etc.
        """
        context = {
            'recent_value': None,
            'change_rate': None,
            'trend': 'unknown',
            'multiple_anomalies': False,
            'sensor_type': None,
            'historical_avg': None,
            'time_of_day': None
        }
        
        try:
            # Get the sensor reading that triggered this anomaly
            if anomaly_event.sensor_reading:
                context['recent_value'] = anomaly_event.sensor_reading.value
                context['sensor_type'] = anomaly_event.sensor_reading.sensor_type
                context['time_of_day'] = anomaly_event.timestamp.strftime('%H:%M')
                
                # Get previous readings to calculate change rate
                sensor_type = anomaly_event.sensor_reading.sensor_type
                plot = anomaly_event.plot
                
                # Get last 10 readings before this anomaly
                recent_readings = SensorReading.objects.filter(
                    plot=plot,
                    sensor_type=sensor_type,
                    timestamp__lt=anomaly_event.sensor_reading.timestamp
                ).order_by('-timestamp')[:10]
                
                if recent_readings.count() >= 2:
                    # Most recent first
                    values = [anomaly_event.sensor_reading.value] + [r.value for r in recent_readings]
                    context['change_rate'] = self._calculate_change_rate(values)
                    context['trend'] = self._determine_trend(values)
                    
                    # Calculate historical average (normal baseline)
                    context['historical_avg'] = round(sum(values) / len(values), 1)
            
            # Check for multiple recent anomalies (stress condition)
            recent_anomalies = AnomalyEvent.objects.filter(
                plot=anomaly_event.plot,
                timestamp__gte=anomaly_event.timestamp - timedelta(hours=3)
            ).count()
            
            context['multiple_anomalies'] = recent_anomalies > 2
            
        except Exception as e:
            print(f"⚠️ Error getting context: {e}")
        
        return context
    
    def _calculate_change_rate(self, values: list) -> float:
        """
        Calculate rate of change from recent values.
        Positive = increasing, Negative = decreasing.
        """
        if len(values) < 2:
            return 0.0
        
        # Calculate percentage change from oldest to most recent
        # values[0] is most recent, values[-1] is oldest
        if values[-1] != 0:
            change = ((values[0] - values[-1]) / values[-1]) * 100
        else:
            change = 0
        
        return round(change, 2)
    
    def _determine_trend(self, values: list) -> str:
        """Determine if values are increasing, decreasing, or stable."""
        if len(values) < 3:
            return 'unknown'
        
        # Check if mostly increasing
        increases = sum(1 for i in range(len(values)-1) if values[i] > values[i+1])
        decreases = sum(1 for i in range(len(values)-1) if values[i] < values[i+1])
        
        total = len(values) - 1
        
        if increases > total * 0.7:
            return 'increasing'
        elif decreases > total * 0.7:
            return 'decreasing'
        else:
            return 'fluctuating'
    
    # ============= MOISTURE ANOMALY RULES =============
    
    def _analyze_moisture_anomaly(self, anomaly: AnomalyEvent, context: Dict) -> Dict:
        """Apply rules specific to moisture anomalies."""
        
        recent_value = context.get('recent_value')
        change_rate = context.get('change_rate', 0)
        trend = context.get('trend')
        severity = anomaly.severity  # 'low', 'medium', 'high' from your ML module
        
        # Handle missing sensor data
        if recent_value is None:
            return {
                'recommended_action': 'Investigate moisture sensor - no recent data available',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    "Moisture anomaly detected but sensor reading data is unavailable. "
                    "Check sensor connectivity and verify data collection."
                ),
                'confidence': anomaly.model_confidence * 0.5,
                'priority': 'medium'
            }
        
        # RULE 1: Critical low moisture (drought stress) - HIGHEST PRIORITY
        if recent_value < self.critical_thresholds['moisture']['critical_low']:
            return {
                'recommended_action': 'URGENT: Immediate irrigation required - crops under severe drought stress',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    f"Soil moisture critically low at {recent_value:.1f}% "
                    f"(normal range: {self.normal_ranges['moisture']['min']}-{self.normal_ranges['moisture']['max']}%). "
                    f"Crops are experiencing severe drought stress and may suffer permanent damage."
                ),
                'confidence': min(anomaly.model_confidence + 0.15, 1.0),
                'priority': 'high'
            }
        
        # RULE 2: Sudden moisture drop (irrigation failure)
        if change_rate < -10:
            return {
                'recommended_action': 'Check irrigation system immediately - possible failure or leak detected',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    f"Soil moisture dropped {abs(change_rate):.1f}% rapidly. "
                    f"This sudden decline indicates possible irrigation system failure, pipe leak, or pump malfunction. "
                    f"Current moisture level: {recent_value:.1f}%."
                ),
                'confidence': self._calculate_confidence(anomaly.model_confidence, change_rate),
                'priority': 'high' if severity == 'high' else 'medium'
            }
        
        # RULE 3: Gradual moisture decline (inefficient irrigation)
        if trend == 'decreasing' and change_rate < -5:
            return {
                'recommended_action': 'Adjust irrigation schedule - gradual moisture loss detected',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    f"Gradual moisture decline detected ({change_rate:.1f}% change over recent period). "
                    f"Current level: {recent_value:.1f}%. "
                    f"Consider increasing irrigation frequency or duration."
                ),
                'confidence': anomaly.model_confidence,
                'priority': 'medium'
            }
        
        # RULE 4: Excessive moisture (overwatering)
        if recent_value > self.critical_thresholds['moisture']['critical_high']:
            return {
                'recommended_action': 'Reduce irrigation immediately - overwatering detected',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    f"Soil moisture excessive at {recent_value:.1f}% (above {self.critical_thresholds['moisture']['critical_high']}%). "
                    f"Risk of root rot, fungal diseases, and oxygen deprivation. Reduce watering and improve drainage."
                ),
                'confidence': anomaly.model_confidence,
                'priority': 'medium'
            }
        
        # RULE 5: Moderate moisture anomaly
        if severity == 'medium':
            return {
                'recommended_action': 'Monitor moisture levels closely and prepare irrigation adjustments',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    f"Moisture anomaly detected with medium severity. Current level: {recent_value:.1f}%. "
                    f"Monitor situation and be ready to adjust irrigation if condition worsens."
                ),
                'confidence': anomaly.model_confidence,
                'priority': 'medium'
            }
        
        # Default rule
        return {
            'recommended_action': 'Monitor soil moisture levels',
            'explanation_text': self._build_explanation(
                anomaly,
                context,
                f"Moisture anomaly detected. Current level: {recent_value:.1f}%. Continue monitoring for changes."
            ),
            'confidence': anomaly.model_confidence * 0.8,
            'priority': 'low'
        }
    
    # ============= TEMPERATURE ANOMALY RULES =============
    
    def _analyze_temperature_anomaly(self, anomaly: AnomalyEvent, context: Dict) -> Dict:
        """Apply rules specific to temperature anomalies."""
        
        recent_value = context.get('recent_value')
        change_rate = context.get('change_rate', 0)
        severity = anomaly.severity
        
        # Handle missing sensor data
        if recent_value is None:
            return {
                'recommended_action': 'Investigate temperature sensor - no recent data available',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    "Temperature anomaly detected but sensor reading data is unavailable. "
                    "Check sensor connectivity and verify data collection."
                ),
                'confidence': anomaly.model_confidence * 0.5,
                'priority': 'medium'
            }
        
        # RULE 1: Extreme high temperature (heat stress)
        if recent_value > self.critical_thresholds['temperature']['critical_high']:
            explanation = (
                f"Extreme temperature detected at {recent_value:.1f}°C "
                f"(normal range: {self.normal_ranges['temperature']['min']}-{self.normal_ranges['temperature']['max']}°C). "
            )
            
            # Add historical comparison if available
            if context.get('historical_avg'):
                diff = recent_value - context['historical_avg']
                explanation += f"This is {diff:.1f}°C above recent average ({context['historical_avg']:.1f}°C). "
            
            # Add trend
            if context.get('trend') == 'increasing':
                explanation += "Temperature continues to rise, worsening heat stress conditions. "
            
            explanation += (
                "Crops at high risk of heat stress, wilting, and reduced yields. "
                "Immediate action required to prevent permanent damage."
            )
            
            return {
                'recommended_action': 'URGENT: Heat stress mitigation - increase irrigation immediately and provide shade',
                'explanation_text': self._build_explanation(anomaly, context, explanation),
                'confidence': min(anomaly.model_confidence + 0.15, 1.0),
                'priority': 'high'
            }
        
        # RULE 2: Low temperature (cold stress/frost risk)
        if recent_value and recent_value < self.critical_thresholds['temperature']['critical_low']:
            return {
                'recommended_action': 'URGENT: Cold protection required - risk of frost damage',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    f"Low temperature detected at {recent_value:.1f}°C. "
                    f"Risk of cold stress, frost damage, and potential crop loss. "
                    f"Consider protective measures such as row covers, heaters, or frost protection sprinklers."
                ),
                'confidence': min(anomaly.model_confidence + 0.15, 1.0),
                'priority': 'high'
            }
        
        # RULE 3: Sudden temperature spike
        if change_rate > 15:
            return {
                'recommended_action': 'Monitor crops closely - sudden temperature increase detected',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    f"Sudden temperature increase of {change_rate:.1f}°C detected. "
                    f"Current temperature: {recent_value:.1f}°C. "
                    f"Monitor crop response and increase irrigation if needed."
                ),
                'confidence': anomaly.model_confidence,
                'priority': 'high' if severity == 'high' else 'medium'
            }
        
        # RULE 4: Sudden temperature drop
        if change_rate < -15:
            return {
                'recommended_action': 'Monitor for cold stress - sudden temperature drop detected',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    f"Sudden temperature decrease of {abs(change_rate):.1f}°C detected. "
                    f"Current temperature: {recent_value:.1f}°C. "
                    f"Monitor for signs of cold stress."
                ),
                'confidence': anomaly.model_confidence,
                'priority': 'medium'
            }
        
        # RULE 5: Moderate temperature anomaly
        if severity == 'medium':
            return {
                'recommended_action': 'Monitor temperature trends and crop response',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    f"Temperature anomaly detected at {recent_value:.1f}°C. "
                    f"Continue monitoring for sustained deviations."
                ),
                'confidence': anomaly.model_confidence,
                'priority': 'medium'
            }
        
        # Default
        return {
            'recommended_action': 'Monitor temperature levels',
            'explanation_text': self._build_explanation(
                anomaly,
                context,
                f"Temperature anomaly detected at {recent_value:.1f}°C. Continue routine monitoring."
            ),
            'confidence': anomaly.model_confidence * 0.8,
            'priority': 'low'
        }
    
    # ============= HUMIDITY ANOMALY RULES =============
    
    def _analyze_humidity_anomaly(self, anomaly: AnomalyEvent, context: Dict) -> Dict:
        """Apply rules specific to humidity anomalies."""
        
        recent_value = context.get('recent_value')
        severity = anomaly.severity
        
        # RULE 1: Very low humidity (dry conditions)
        if recent_value and recent_value < self.critical_thresholds['humidity']['critical_low']:
            return {
                'recommended_action': 'Increase humidity or irrigation - risk of plant stress from dry air',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    f"Very low humidity at {recent_value:.1f}% "
                    f"(normal range: {self.normal_ranges['humidity']['min']}-{self.normal_ranges['humidity']['max']}%). "
                    f"Dry conditions may cause increased transpiration, water stress, and leaf damage. "
                    f"Consider misting or increasing irrigation."
                ),
                'confidence': anomaly.model_confidence,
                'priority': 'high' if severity == 'high' else 'medium'
            }
        
        # RULE 2: Very high humidity (disease risk)
        if recent_value and recent_value > self.critical_thresholds['humidity']['critical_high']:
            return {
                'recommended_action': 'Improve ventilation urgently - high humidity increases disease risk',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    f"High humidity at {recent_value:.1f}% (above {self.critical_thresholds['humidity']['critical_high']}%). "
                    f"Elevated risk of fungal diseases, mold, and bacterial infections. "
                    f"Improve air circulation, reduce watering frequency if possible, and monitor for disease symptoms."
                ),
                'confidence': anomaly.model_confidence,
                'priority': 'high' if severity == 'high' else 'medium'
            }
        
        # RULE 3: Moderate humidity anomaly
        if severity == 'medium':
            return {
                'recommended_action': 'Monitor humidity levels and ventilation',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    f"Humidity anomaly detected at {recent_value:.1f}%. "
                    f"Monitor for changes and ensure adequate ventilation."
                ),
                'confidence': anomaly.model_confidence,
                'priority': 'medium'
            }
        
        # Default
        return {
            'recommended_action': 'Monitor humidity levels',
            'explanation_text': self._build_explanation(
                anomaly,
                context,
                f"Humidity anomaly detected at {recent_value:.1f}%. Continue routine monitoring."
            ),
            'confidence': anomaly.model_confidence * 0.8,
            'priority': 'low'
        }
    
    # ============= GENERIC ANOMALY RULES =============
    
    def _analyze_generic_anomaly(self, anomaly: AnomalyEvent, context: Dict) -> Dict:
        """Fallback rules for unclassified anomalies."""
        
        severity = anomaly.severity
        
        # RULE 1: Multiple anomalies (combined stress)
        if context.get('multiple_anomalies'):
            return {
                'recommended_action': 'URGENT: Comprehensive plot inspection - multiple stress factors detected',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    "Multiple anomalies detected in short timeframe. "
                    "This indicates combined stress factors affecting the plot. "
                    "Conduct thorough inspection of irrigation, environmental conditions, and crop health."
                ),
                'confidence': anomaly.model_confidence * 0.9,
                'priority': 'high'
            }
        
        # RULE 2: Low confidence anomaly
        if anomaly.model_confidence < 0.6:
            return {
                'recommended_action': 'Verify with manual inspection - anomaly detected with moderate confidence',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    f"Anomaly detected with moderate confidence ({anomaly.model_confidence:.2f}). "
                    f"Manual inspection recommended to confirm sensor readings and identify any issues."
                ),
                'confidence': anomaly.model_confidence,
                'priority': 'low'
            }
        
        # RULE 3: High severity unknown anomaly
        if severity == 'high':
            return {
                'recommended_action': 'Investigate anomaly urgently - high severity detected',
                'explanation_text': self._build_explanation(
                    anomaly,
                    context,
                    f"High severity anomaly detected. Immediate investigation recommended."
                ),
                'confidence': anomaly.model_confidence,
                'priority': 'high'
            }
        
        # Default
        return {
            'recommended_action': 'Investigate anomaly condition',
            'explanation_text': self._build_explanation(
                anomaly,
                context,
                "Anomaly detected in sensor data. Further investigation recommended to identify cause."
            ),
            'confidence': anomaly.model_confidence,
            'priority': 'medium' if severity == 'medium' else 'low'
        }
    
    # ============= HELPER METHODS =============
    
    def _build_explanation(self, anomaly: AnomalyEvent, context: Dict, detail: str) -> str:
        """
        Build a human-readable explanation.
        
        Includes: timestamp, model confidence, specific details, trend, and change rate.
        """
        timestamp_str = anomaly.timestamp.strftime("%Y-%m-%d at %H:%M")
        sensor_type = context.get('sensor_type', 'sensor')
        
        # Basic explanation
        explanation = (
            f"On {timestamp_str}, {sensor_type} readings detected a {anomaly.anomaly_type} "
            f"(ML model confidence: {anomaly.model_confidence:.2f}, severity: {anomaly.severity}). "
            f"{detail}"
        )
        
        # Add trend if available
        if context.get('trend') and context['trend'] != 'unknown':
            trend_desc = {
                'increasing': 'Values are rising',
                'decreasing': 'Values are declining',
                'fluctuating': 'Values are unstable'
            }.get(context['trend'], context['trend'])
            explanation += f" Trend: {trend_desc}."
        
        # Add change rate if significant
        if context.get('change_rate') and abs(context['change_rate']) > 5:
            explanation += f" Change rate: {context['change_rate']:+.1f}%."
        
        # Add multi-factor warning
        if context.get('multiple_anomalies'):
            explanation += " ⚠️ Multiple anomalies detected - investigate for combined stress factors."
        
        return explanation
    
    def _calculate_confidence(self, model_confidence: float, change_rate: float) -> float:
        """
        Calculate agent confidence based on model confidence and change severity.
        Higher change rates increase confidence in critical situations.
        """
        # If change is severe, boost confidence
        if abs(change_rate) > 20:
            confidence = min(model_confidence + 0.2, 1.0)
        elif abs(change_rate) > 15:
            confidence = min(model_confidence + 0.15, 1.0)
        elif abs(change_rate) > 10:
            confidence = min(model_confidence + 0.1, 1.0)
        else:
            confidence = model_confidence
        
        return round(confidence, 2)