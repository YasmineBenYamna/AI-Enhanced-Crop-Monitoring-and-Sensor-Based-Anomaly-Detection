"""
Anomaly Injection Scenarios for Sensor Simulator
Implements 3 core anomaly patterns for reproducible testing:
1. Sudden drops - simulate irrigation failure (moisture drops rapidly)
2. Spikes - simulate sensor malfunction or extreme events
3. Drift - gradual sensor calibration drift over time

IN THIS FILE WE DEFINE A MOTHER CLASS : ANOMALYSCENARIO AND 3 CHILD CLASSES FOR EACH SCENARIO TYPE. THE KEY FUNCTION IS MODIFIY_READING .
"""

from typing import Dict, List
from datetime import datetime
import numpy as np


class AnomalyScenario:
    """Base class for anomaly scenarios."""
    
    def __init__(self, name: str, description: str, 
                 start_hour: float, duration_minutes: float):
        """
        Initialize anomaly scenario.
        
        Args:
            name: Scenario name
            description: Human-readable description
            start_hour: Hours after simulation start to begin anomaly
            duration_minutes: Duration of anomaly in minutes
        """
        self.name = name
        self.description = description
        self.start_hour = start_hour
        self.duration_minutes = duration_minutes
        self.is_active = False
        self.start_time = None
    
    def should_activate(self, hours_since_start: float) -> bool:
        """Check if anomaly should activate."""
        return hours_since_start >= self.start_hour and not self.is_active
    
    def is_expired(self) -> bool:
        """Check if anomaly duration has expired."""
        if not self.is_active or not self.start_time:
            return False
        
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        return elapsed >= self.duration_minutes
    
    def activate(self):
        """Activate the anomaly."""
        self.is_active = True
        self.start_time = datetime.now()
        print(f"\n🚨 ANOMALY ACTIVATED: {self.name}")
        print(f"   Description: {self.description}")
        print(f"   Duration: {self.duration_minutes} minutes")
    
    def deactivate(self):
        """Deactivate the anomaly."""
        self.is_active = False
        print(f"\n✅ ANOMALY ENDED: {self.name}")
    
    def modify_reading(self, sensor_type: str, normal_value: float) -> float:
        """
       This method takes a normal sensor value and changes it to simulate an anomaly
        """
        return normal_value


class SuddenDropScenario(AnomalyScenario):
    """
    Scenario 1: Sudden drops - simulate irrigation failure
    Effect: Moisture drops rapidly (>10% in short time)
    """
    
    def __init__(self, start_hour: float = 2.0, duration_minutes: float = 180,
                 target_drop: float = 15.0):
        """
        Initialize sudden drop scenario.
        
        Args:
            start_hour: When to start the anomaly
            duration_minutes: How long the drop occurs
            target_drop: Total percentage drop to simulate
        """
        super().__init__(
            name="Sudden Drop (Irrigation Failure)",
            description="Simulates irrigation system failure with rapid moisture loss",
            start_hour=start_hour,
            duration_minutes=duration_minutes
        )
        self.target_drop = target_drop
    
    def modify_reading(self, sensor_type: str, normal_value: float) -> float:
        if not self.is_active:
            return normal_value
        
        if sensor_type == 'moisture':
            # Calculate progressive drop over time
            elapsed_minutes = (datetime.now() - self.start_time).total_seconds() / 60
            progress = min(1.0, elapsed_minutes / self.duration_minutes)
            
            # Rapid exponential drop
            drop = self.target_drop * (1 - np.exp(-3 * progress))
            
            # Ensure we don't go below minimum
            return max(30.0, normal_value - drop)
        
        return normal_value


class SpikeScenario(AnomalyScenario):
    """
    Scenario 2: Spikes - simulate sensor malfunction or extreme events
    Effect: Random extreme spikes in sensor readings
    """
    
    def __init__(self, start_hour: float = 4.0, duration_minutes: float = 120,
                 spike_probability: float = 0.3, affected_sensor: str = 'all'):
        """
        Initialize spike scenario.
        
        Args:
            start_hour: When to start the anomaly
            duration_minutes: How long spikes occur
            spike_probability: Probability of spike per reading (0.0-1.0)
            affected_sensor: Which sensor to affect ('moisture', 'temperature', 'humidity', 'all')
        """
        super().__init__(
            name="Spikes (Sensor Malfunction)",
            description=f"Simulates sensor malfunction with random spikes in {affected_sensor} readings",
            start_hour=start_hour,
            duration_minutes=duration_minutes
        )
        self.spike_probability = spike_probability
        self.affected_sensor = affected_sensor
    
    def modify_reading(self, sensor_type: str, normal_value: float) -> float:
        if not self.is_active:
            return normal_value
        
        # Check if this sensor should be affected
        if self.affected_sensor != 'all' and sensor_type != self.affected_sensor:
            return normal_value
        
        # Random spike occurs
        if np.random.random() < self.spike_probability:
            if sensor_type == 'moisture':
                # Random extreme moisture spike (very high or very low)
                return np.random.choice([
                    np.random.uniform(10, 25),   # Extremely low
                    np.random.uniform(85, 95)    # Extremely high
                ])
            
            elif sensor_type == 'temperature':
                # Random temperature spike
                return np.random.choice([
                    np.random.uniform(0, 8),     # Extremely cold
                    np.random.uniform(38, 45)    # Extremely hot
                ])
            
            elif sensor_type == 'humidity':
                # Random humidity spike
                return np.random.choice([
                    np.random.uniform(10, 20),   # Extremely dry
                    np.random.uniform(90, 98)    # Extremely humid
                ])
        
        return normal_value


class DriftScenario(AnomalyScenario):
    """
    Scenario 3: Drift - gradual sensor calibration drift over time
    Effect: Sensor readings gradually shift from true values
    """
    
    def __init__(self, start_hour: float = 6.0, duration_minutes: float = 360,
                 drift_amount: float = 20.0, drift_direction: str = 'up',
                 affected_sensor: str = 'temperature'):
        """
        Initialize drift scenario.
        
        Args:
            start_hour: When to start the anomaly
            duration_minutes: How long drift occurs
            drift_amount: Total drift amount (percentage or degrees)
            drift_direction: 'up' or 'down'
            affected_sensor: Which sensor to affect
        """
        super().__init__(
            name=f"Drift (Calibration Drift - {affected_sensor})",
            description=f"Simulates gradual {drift_direction}ward drift in {affected_sensor} sensor",
            start_hour=start_hour,
            duration_minutes=duration_minutes
        )
        self.drift_amount = drift_amount
        self.drift_direction = drift_direction
        self.affected_sensor = affected_sensor
    
    def modify_reading(self, sensor_type: str, normal_value: float) -> float:
        if not self.is_active:
            return normal_value
        
        if sensor_type != self.affected_sensor:
            return normal_value
        
        # Calculate gradual drift over time
        elapsed_minutes = (datetime.now() - self.start_time).total_seconds() / 60
        progress = min(1.0, elapsed_minutes / self.duration_minutes)
        
        # Linear drift
        drift = self.drift_amount * progress
        
        if self.drift_direction == 'down':
            drift = -drift
        
        return normal_value + drift


class AnomalyManager:
    """Manages multiple anomaly scenarios."""
    
    def __init__(self):
        self.scenarios: List[AnomalyScenario] = []
        self.simulation_start = datetime.now()
    
    def add_scenario(self, scenario: AnomalyScenario):
        """Add an anomaly scenario."""
        self.scenarios.append(scenario)
        print(f"📋 Registered scenario: {scenario.name} "
              f"(starts at hour {scenario.start_hour}, "
              f"duration {scenario.duration_minutes}min)")
    
    def get_hours_since_start(self) -> float:
        """Get hours since simulation start."""
        return (datetime.now() - self.simulation_start).total_seconds() / 3600
    
    def update(self):
        """Update all scenarios - activate/deactivate based on time."""
        hours = self.get_hours_since_start()
        
        for scenario in self.scenarios:
            # Check activation
            if scenario.should_activate(hours):
                scenario.activate()
            
            # Check expiration
            if scenario.is_expired():
                scenario.deactivate()
    
    def modify_reading(self, sensor_type: str, normal_value: float) -> float:
        """
        Apply all active anomalies to a sensor reading.
        
        Args:
            sensor_type: Type of sensor
            normal_value: Normal sensor value
            
        Returns:
            Modified value with anomalies applied
        """
        modified_value = normal_value
        
        for scenario in self.scenarios:
            if scenario.is_active:
                modified_value = scenario.modify_reading(sensor_type, modified_value)
        
        return modified_value
    
    def get_active_scenarios(self) -> List[str]:
        """Get list of currently active scenario names."""
        return [s.name for s in self.scenarios if s.is_active]
    
    def has_active_anomalies(self) -> bool:
        """Check if any anomalies are currently active."""
        return any(s.is_active for s in self.scenarios)


# ============================================================================
# PREDEFINED TEST SCENARIOS - Ready to use!
# ============================================================================

def create_irrigation_failure_test() -> AnomalyManager:
    """
    Test Scenario: Irrigation system failure
    - Starts 1 hour after simulation begins
    - Moisture drops rapidly over 2 hours
    """
    manager = AnomalyManager()
    manager.add_scenario(
        SuddenDropScenario(
            start_hour=1.0,
            duration_minutes=120,
            target_drop=15.0
        )
    )
    return manager


def create_sensor_malfunction_test() -> AnomalyManager:
    """
    Test Scenario: Sensor malfunction with random spikes
    - Starts 2 hours after simulation begins
    - Random spikes for 1.5 hours
    - Affects all sensors
    """
    manager = AnomalyManager()
    manager.add_scenario(
        SpikeScenario(
            start_hour=2.0,
            duration_minutes=90,
            spike_probability=0.4,
            affected_sensor='all'
        )
    )
    return manager


def create_calibration_drift_test() -> AnomalyManager:
    """
    Test Scenario: Temperature sensor calibration drift
    - Starts 3 hours after simulation begins
    - Gradual upward drift over 4 hours
    """
    manager = AnomalyManager()
    manager.add_scenario(
        DriftScenario(
            start_hour=3.0,
            duration_minutes=240,
            drift_amount=12.0,
            drift_direction='up',
            affected_sensor='temperature'
        )
    )
    return manager


def create_full_test_suite() -> AnomalyManager:
    """
    Comprehensive test with all 3 anomaly types (staggered timing).
    Total duration: ~7 hours
    
    Timeline:
    - Hour 1-3: Irrigation failure (sudden drop in moisture)
    - Hour 3-4.5: Sensor spikes (random malfunctions)
    - Hour 5-9: Temperature drift (gradual calibration drift)
    """
    manager = AnomalyManager()
    
    # 1. Sudden drop (irrigation failure)
    manager.add_scenario(
        SuddenDropScenario(
            start_hour=1.0,
            duration_minutes=120,
            target_drop=15.0
        )
    )
    
    # 2. Spikes (sensor malfunction)
    manager.add_scenario(
        SpikeScenario(
            start_hour=3.0,
            duration_minutes=90,
            spike_probability=0.3,
            affected_sensor='temperature'
        )
    )
    
    # 3. Drift (calibration drift)
    manager.add_scenario(
        DriftScenario(
            start_hour=5.0,
            duration_minutes=240,
            drift_amount=15.0,
            drift_direction='up',
            affected_sensor='humidity'
        )
    )
    
    return manager


def create_quick_test() -> AnomalyManager:
    """
    Quick test for rapid validation (~2 hours).
    
    Timeline:
    - Hour 0.25: Irrigation failure (30 min)
    - Hour 1.0: Sensor spikes (30 min)
    - Hour 1.5: Drift (30 min)
    """
    manager = AnomalyManager()
    
    manager.add_scenario(
        SuddenDropScenario(start_hour=0.25, duration_minutes=30, target_drop=12.0)
    )
    
    manager.add_scenario(
        SpikeScenario(start_hour=1.0, duration_minutes=30, 
                     spike_probability=0.5, affected_sensor='all')
    )
    
    manager.add_scenario(
        DriftScenario(start_hour=1.5, duration_minutes=30,
                     drift_amount=10.0, drift_direction='up', 
                     affected_sensor='moisture')
    )
    
    return manager


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("ANOMALY INJECTION SCENARIOS - 3 Core Types")
    print("=" * 80)
    
    print("\n📋 Available Scenarios:\n")
    
    scenarios = [
        ("1. Sudden Drops", "Simulate irrigation failure (moisture drops rapidly)"),
        ("2. Spikes", "Simulate sensor malfunction or extreme events"),
        ("3. Drift", "Gradual sensor calibration drift over time"),
    ]
    
    for name, desc in scenarios:
        print(f"  {name}")
        print(f"     {desc}\n")
    
    print("=" * 80)
    print("PREDEFINED TEST SUITES")
    print("=" * 80)
    
    print("\n1. create_irrigation_failure_test()")
    print("   Test sudden moisture drop over 2 hours")
    
    print("\n2. create_sensor_malfunction_test()")
    print("   Test random sensor spikes over 1.5 hours")
    
    print("\n3. create_calibration_drift_test()")
    print("   Test gradual temperature drift over 4 hours")
    
    print("\n4. create_full_test_suite()")
    print("   Comprehensive test with all 3 types (~7 hours)")
    
    print("\n5. create_quick_test()")
    print("   Quick validation test (~2 hours)")
    
    print("\n" + "=" * 80)
    print("Integration: Use with sensor_simulator_enhanced.py")
    print("=" * 80 + "\n")