"""
FAST Anomaly Injection Scenarios for Sensor Simulator
Modified version: All scenarios happen FAST (within 15 minutes)
Perfect for quick testing and demos!

Changes from original:
- All scenarios start IMMEDIATELY (start_hour = 0.0)
- All durations reduced to 10-15 minutes
- Drops/spikes/drifts are MORE DRAMATIC for easy detection
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
    Effect: Moisture drops rapidly (>20% in short time)
    FAST VERSION: Drops dramatically within 10 minutes!
    """
    
    def __init__(self, start_hour: float = 0.0, duration_minutes: float = 15,
                 target_drop: float = 25.0):
        """
        Initialize sudden drop scenario.
        
        Args:
            start_hour: When to start the anomaly (default: IMMEDIATELY)
            duration_minutes: How long the drop occurs (default: 15 min)
            target_drop: Total percentage drop to simulate (default: 25%)
        """
        super().__init__(
            name="FAST Irrigation Failure",
            description="Simulates irrigation system failure with RAPID moisture loss",
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
            
            # FAST exponential drop (more aggressive than original)
            drop = self.target_drop * (1 - np.exp(-5 * progress))  # Changed from -3 to -5
            
            # Allow lower minimum for more dramatic effect
            return max(25.0, normal_value - drop)  # Changed from 30.0 to 25.0
        
        return normal_value


class SpikeScenario(AnomalyScenario):
    """
    Scenario 2: Spikes - simulate sensor malfunction or extreme events
    Effect: Random extreme spikes in sensor readings
    FAST VERSION: Higher spike probability for immediate detection!
    """
    
    def __init__(self, start_hour: float = 0.0, duration_minutes: float = 15,
                 spike_probability: float = 0.5, affected_sensor: str = 'all'):
        """
        Initialize spike scenario.
        
        Args:
            start_hour: When to start the anomaly (default: IMMEDIATELY)
            duration_minutes: How long spikes occur (default: 15 min)
            spike_probability: Probability of spike per reading (default: 50%)
            affected_sensor: Which sensor to affect ('moisture', 'temperature', 'humidity', 'all')
        """
        super().__init__(
            name="FAST Sensor Malfunction",
            description=f"Simulates sensor malfunction with frequent spikes in {affected_sensor} readings",
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
        
        # Random spike occurs (50% chance by default - very frequent!)
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
    FAST VERSION: Drifts quickly within 15 minutes!
    """
    
    def __init__(self, start_hour: float = 0.0, duration_minutes: float = 15,
                 drift_amount: float = 20.0, drift_direction: str = 'up',
                 affected_sensor: str = 'temperature'):
        """
        Initialize drift scenario.
        
        Args:
            start_hour: When to start the anomaly (default: IMMEDIATELY)
            duration_minutes: How long drift occurs (default: 15 min)
            drift_amount: Total drift amount (percentage or degrees, default: 20)
            drift_direction: 'up' or 'down'
            affected_sensor: Which sensor to affect:temperature
        """
        super().__init__(
            name=f"FAST Calibration Drift - {affected_sensor}",
            description=f"Simulates rapid {drift_direction}ward drift in {affected_sensor} sensor",
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
        
        # Accelerated drift (quadratic instead of linear for faster effect)
        drift = self.drift_amount * (progress ** 1.5)  # Accelerates over time
        
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
# FAST PREDEFINED TEST SCENARIOS - All complete within 15 minutes!
# ============================================================================

def create_irrigation_failure_test() -> AnomalyManager:
    """
    FAST Test: Irrigation system failure
    - Starts IMMEDIATELY
    - Moisture drops from ~60% to ~35% in 15 minutes
    - Very easy to detect!
    """
    manager = AnomalyManager()
    manager.add_scenario(
        SuddenDropScenario(
            start_hour=0.0,        # ← IMMEDIATE START!
            duration_minutes=15,    # ← 15 min total
            target_drop=25.0       # ← 25% drop (60% → 35%)
        )
    )
    return manager


def create_sensor_malfunction_test() -> AnomalyManager:
    """
    FAST Test: Sensor malfunction with random spikes
    - Starts IMMEDIATELY
    - 50% of readings will be spikes
    - Runs for 15 minutes
    - Affects all sensors
    """
    manager = AnomalyManager()
    manager.add_scenario(
        SpikeScenario(
            start_hour=0.0,           # ← IMMEDIATE START!
            duration_minutes=15,       # ← 15 min total
            spike_probability=0.5,     # ← 50% spike rate!
            affected_sensor='all'
        )
    )
    return manager


def create_calibration_drift_test() -> AnomalyManager:
    """
    FAST Test: Temperature sensor calibration drift
    - Starts IMMEDIATELY
    - Drifts +20°C over 15 minutes
    - Very obvious pattern
    """
    manager = AnomalyManager()
    manager.add_scenario(
        DriftScenario(
            start_hour=0.0,           # ← IMMEDIATE START!
            duration_minutes=15,       # ← 15 min total
            drift_amount=20.0,         # ← +20°C drift
            drift_direction='up',
            affected_sensor='temperature'
        )
    )
    return manager


def create_full_test_suite() -> AnomalyManager:
    """
    FAST Comprehensive test with all 3 anomaly types (overlapping).
    Total duration: 15 minutes
    
    Timeline:
    - Minute 0-15: Irrigation failure (moisture drops)
    - Minute 0-15: Temperature spikes (overlapping)
    - Minute 0-15: Humidity drift (overlapping)
    
    All happening at once for maximum anomalies!
    """
    manager = AnomalyManager()
    
    # 1. Sudden drop (irrigation failure)
    manager.add_scenario(
        SuddenDropScenario(
            start_hour=0.0,
            duration_minutes=15,
            target_drop=25.0
        )
    )
    
    # 2. Spikes (sensor malfunction)
    manager.add_scenario(
        SpikeScenario(
            start_hour=0.0,
            duration_minutes=15,
            spike_probability=0.4,
            affected_sensor='temperature'
        )
    )
    
    # 3. Drift (calibration drift)
    manager.add_scenario(
        DriftScenario(
            start_hour=0.0,
            duration_minutes=15,
            drift_amount=20.0,
            drift_direction='up',
            affected_sensor='humidity'
        )
    )
    
    return manager


def create_quick_test() -> AnomalyManager:
    """
    FAST Quick test - All anomalies in 15 minutes (sequential).
    
    Timeline:
    - Minute 0-5: Irrigation failure
    - Minute 5-10: Sensor spikes
    - Minute 10-15: Drift
    """
    manager = AnomalyManager()
    
    manager.add_scenario(
        SuddenDropScenario(start_hour=0.0, duration_minutes=5, target_drop=20.0)
    )
    
    manager.add_scenario(
        SpikeScenario(start_hour=0.083, duration_minutes=5,  # 0.083 hours = 5 min
                     spike_probability=0.6, affected_sensor='all')
    )
    
    manager.add_scenario(
        DriftScenario(start_hour=0.167, duration_minutes=5,  # 0.167 hours = 10 min
                     drift_amount=15.0, drift_direction='down', 
                     affected_sensor='moisture')
    )
    
    return manager


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("FAST ANOMALY INJECTION SCENARIOS - All Complete in 15 Minutes!")
    print("=" * 80)
    
    print("\n📋 Available Scenarios:\n")
    
    scenarios = [
        ("1. Sudden Drops", "Moisture drops 25% in 15 minutes (60% → 35%)"),
        ("2. Spikes", "50% of readings are extreme spikes"),
        ("3. Drift", "Temperature/humidity drifts +20 in 15 minutes"),
    ]
    
    for name, desc in scenarios:
        print(f"  {name}")
        print(f"     {desc}\n")
    
    print("=" * 80)
    print("FAST PREDEFINED TEST SUITES")
    print("=" * 80)
    
    print("\n1. create_irrigation_failure_test()")
    print("   Immediate moisture drop over 15 minutes")
    print("   Result: ~60% of windows will be anomalies")
    
    print("\n2. create_sensor_malfunction_test()")
    print("   Immediate random sensor spikes for 15 minutes")
    print("   Result: ~50% of readings will be spikes")
    
    print("\n3. create_calibration_drift_test()")
    print("   Immediate temperature drift for 15 minutes")
    print("   Result: ~70% of windows will be anomalies")
    
    print("\n4. create_full_test_suite()")
    print("   All 3 anomalies happening at once for 15 minutes")
    print("   Result: ~80% of windows will be anomalies!")
    
    print("\n5. create_quick_test()")
    print("   All 3 anomalies sequential (5 min each)")
    print("   Result: ~60% of windows will be anomalies")
    
    print("\n" + "=" * 80)
    print("Perfect for quick testing and demos!")
    print("=" * 80 + "\n")