"""
Enhanced Sensor Data Simulator with Anomaly Injection
Real-time simulator with optional turbo mode.
Usage: python sensor_simulator.py --scenario [test_name] --duration [hours]
"""

import requests
import time
import numpy as np
from datetime import datetime, timedelta
import argparse
from typing import Dict, List
import math
from simulator_config import SimulatorConfig
from anomaly_scenarios import (
    AnomalyManager,
    create_irrigation_failure_test,
    create_sensor_malfunction_test,
    create_calibration_drift_test,
    create_full_test_suite,
    create_quick_test
)


class SensorSimulator:
    """
    Enhanced sensor simulator with anomaly injection capabilities.
    Extends baseline simulation with configurable anomaly scenarios.
    """
    
    def __init__(self, api_url: str, plot_ids: List[int], 
                 interval: int = 300, anomaly_manager: AnomalyManager = None):
        """
        Initialize the enhanced sensor simulator.
        
        Args:
            api_url: Base URL of the Django API
            plot_ids: List of plot IDs to simulate
            interval: Time interval between readings in seconds
            anomaly_manager: Optional AnomalyManager for injecting anomalies
        """
        self.api_url = api_url
        self.plot_ids = plot_ids
        self.interval = interval
        self.start_time = datetime.now()
        
        # Anomaly management
        self.anomaly_manager = anomaly_manager
        
        # Authentication token
        self.auth_token = None
        
        # Load configuration
        self.config = SimulatorConfig
        self.baseline_params = self.config.BASELINE_PARAMS
        
        # Track last irrigation time for each plot
        self.last_irrigation = {plot_id: self.start_time for plot_id in plot_ids}
        
        # Track moisture state for each plot
        self.moisture_state = {
            plot_id: self.baseline_params['moisture']['mean'] 
            for plot_id in plot_ids
        }
        
        # Turbo mode settings
        self.turbo_mode = False
        self.turbo_delay = 0.1
        self.simulate_time = False
    
    def set_auth_token(self, token: str):
        """Set the JWT authentication token."""
        self.auth_token = token
    
    def get_time_of_day(self) -> float:
        """Get current time of day as hours since midnight (0-24)."""
        current_time = datetime.now()
        return current_time.hour + current_time.minute / 60.0
    
    def get_hours_since_start(self) -> float:
        """Get hours since simulation start."""
        return (datetime.now() - self.start_time).total_seconds() / 3600
    
    def generate_temperature(self, time_of_day: float) -> float:
        params = self.baseline_params['temperature']
        
        phase = (time_of_day - params['peak_hour']) * (2 * math.pi / 24)
        temperature = params['mean'] + params['amplitude'] * math.cos(phase)
        
        temperature += np.random.normal(0, params['noise_std'])
        
        return round(temperature, 2)
    
    def generate_humidity(self, temperature: float, time_of_day: float) -> float:
        params = self.baseline_params['humidity']
        temp_params = self.baseline_params['temperature']
        
        phase = (time_of_day - temp_params['peak_hour']) * (2 * math.pi / 24)
        humidity = params['mean'] - params['amplitude'] * math.cos(phase)
        
        temp_deviation = temperature - temp_params['mean']
        humidity += params['temp_correlation'] * temp_deviation
        
        humidity += np.random.normal(0, params['noise_std'])
        
<<<<<<< HEAD
        humidity = max(20.0, min(95.0, humidity))
=======
        humidity = max(20.0, min(95.0, humidity))  # ← This line already exists
>>>>>>> e8a40c8f3d9629e6a162fd096acb6bf76baa3f42
        
        return round(humidity, 2)
    
    def generate_moisture(self, plot_id: int) -> float:
        """Generate realistic soil moisture reading with irrigation cycles."""
        params = self.baseline_params['moisture']
        
        # Get current moisture state
        current_moisture = self.moisture_state[plot_id]
        
        # Check if irrigation should occur
        hours_since_irrigation = (
            datetime.now() - self.last_irrigation[plot_id]
        ).total_seconds() / 3600
        
        # Irrigation interval: 18 ± 4 hours
        irrigation_interval = (
            self.config.IRRIGATION_INTERVAL_HOURS + 
            np.random.uniform(
                -self.config.IRRIGATION_VARIANCE_HOURS,
                self.config.IRRIGATION_VARIANCE_HOURS
            )
        )
        
        if hours_since_irrigation >= irrigation_interval:
            # Irrigation event - increase moisture
            current_moisture += params['irrigation_boost']
            self.last_irrigation[plot_id] = datetime.now()
            print(f"💧 [IRRIGATION] Plot {plot_id} irrigated at {datetime.now().strftime('%H:%M:%S')}")
        
        # Gradual decrease during day
        decay = params['decay_rate'] * (self.interval / 3600)
        current_moisture -= decay
        
        # Add random noise
        current_moisture += np.random.normal(0, params['noise_std'])
    
<<<<<<< HEAD
        current_moisture = max(30.0, min(80.0, current_moisture))
=======
        current_moisture = max(30.0, min(80.0, current_moisture))  # ← This line exists
>>>>>>> e8a40c8f3d9629e6a162fd096acb6bf76baa3f42
        
        self.moisture_state[plot_id] = current_moisture
        
        return round(current_moisture, 2)
    
    def apply_anomalies(self, sensor_type: str, normal_value: float) -> float:
        """
        Apply anomaly modifications to a normal sensor reading.
        
        Args:
            sensor_type: Type of sensor (moisture, temperature, humidity)
            normal_value: Normal sensor value
            
        Returns:
            Modified value with anomalies applied (if any active)
        """
        if self.anomaly_manager:
            return self.anomaly_manager.modify_reading(sensor_type, normal_value)
        return normal_value
    
    def create_sensor_reading(self, plot_id: int, sensor_type: str, 
                             value: float, is_anomalous: bool = False) -> Dict:
        """
        Create a sensor reading payload for the API.
        
        Args:
            plot_id: Plot identifier
            sensor_type: Type of sensor
            value: Sensor value
            is_anomalous: Whether this reading has been modified by anomaly
            
        Returns:
            Dictionary payload for API
        """
        return {
            'plot': plot_id,
            'sensor_type': sensor_type,
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'source': 'simulator_anomaly' if is_anomalous else 'simulator'
        }
    
    def send_reading(self, reading: Dict) -> bool:
        """Send a sensor reading to the Django API."""
        headers = {'Content-Type': 'application/json'}
        
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        try:
            response = requests.post(
                f'{self.api_url}/sensor-readings/',
                json=reading,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return True
            else:
                print(f"❌ Error sending reading: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def simulate_cycle(self):
        """Run one simulation cycle with anomaly injection."""
        time_of_day = self.get_time_of_day()
        hours_since_start = self.get_hours_since_start()
        
        # Update anomaly manager
        if self.anomaly_manager:
            self.anomaly_manager.update()
        
        # Display cycle header (skip in turbo mode)
        if not self.turbo_mode:
            print(f"\n{'='*70}")
            print(f"⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Simulation Cycle")
            print(f"   Time of day: {time_of_day:.2f}h | Hours since start: {hours_since_start:.2f}h")
            
            # Display active anomalies
            if self.anomaly_manager and self.anomaly_manager.has_active_anomalies():
                active = self.anomaly_manager.get_active_scenarios()
                print(f"   🚨 ACTIVE ANOMALIES: {', '.join(active)}")
            
            print(f"{'='*70}")
        
        for plot_id in self.plot_ids:
            if not self.turbo_mode:
                print(f"\n🌾 Plot {plot_id}:")
            
            # Generate normal values
            normal_temperature = self.generate_temperature(time_of_day)
            normal_humidity = self.generate_humidity(normal_temperature, time_of_day)
            normal_moisture = self.generate_moisture(plot_id)
            
            # Apply anomalies
            temperature = self.apply_anomalies('temperature', normal_temperature)
            humidity = self.apply_anomalies('humidity', normal_humidity)
            moisture = self.apply_anomalies('moisture', normal_moisture)
            
            # Check if values were modified
            temp_anomalous = abs(temperature - normal_temperature) > 0.01
            humidity_anomalous = abs(humidity - normal_humidity) > 0.01
            moisture_anomalous = abs(moisture - normal_moisture) > 0.01
            
            # Create and send readings
            readings = [
                (self.create_sensor_reading(plot_id, 'temperature', temperature, temp_anomalous),
                 temp_anomalous, normal_temperature),
                (self.create_sensor_reading(plot_id, 'humidity', humidity, humidity_anomalous),
                 humidity_anomalous, normal_humidity),
                (self.create_sensor_reading(plot_id, 'moisture', moisture, moisture_anomalous),
                 moisture_anomalous, normal_moisture)
            ]
            
            for reading, is_anomalous, normal_val in readings:
                success = self.send_reading(reading)
                
                if not self.turbo_mode:
                    status = "✅" if success else "❌"
                    anomaly_marker = " 🚨 ANOMALY" if is_anomalous else ""
                    
                    # Format value with appropriate unit
                    unit = "°C" if reading['sensor_type'] == 'temperature' else "%"
                    
                    print(f"   {status} {reading['sensor_type']:12s}: {reading['value']:6.2f}{unit}{anomaly_marker}")
                    
                    # Show deviation if anomalous
                    if is_anomalous:
                        deviation = reading['value'] - normal_val
                        print(f"      └─ Normal: {normal_val:6.2f}{unit}, Deviation: {deviation:+6.2f}{unit}")
    
    def run(self, duration_hours: float = None):
        """Run the simulator continuously or for a specified duration."""
        print("\n" + "="*70)
        print("🌾 ENHANCED AGRICULTURAL SENSOR SIMULATOR")
        print("="*70)
        print(f"API URL: {self.api_url}")
        print(f"Plot IDs: {self.plot_ids}")
        print(f"Interval: {self.interval} seconds ({self.interval/60:.1f} minutes)")
        
        if duration_hours:
            print(f"Duration: {duration_hours} hours ({duration_hours * 60:.1f} minutes)")
        else:
            print("Duration: Continuous (Ctrl+C to stop)")
        
        if self.turbo_mode:
            print(f"\n⚡ TURBO MODE ENABLED (delay: {self.turbo_delay}s)")
            if self.simulate_time:
                print("   Using simulated time progression")
        
        if self.anomaly_manager:
            print("\n🔬 ANOMALY INJECTION ENABLED")
            print(f"   Registered scenarios: {len(self.anomaly_manager.scenarios)}")
            for scenario in self.anomaly_manager.scenarios:
                print(f"   • {scenario.name}")
                print(f"     Start: {scenario.start_hour}h | Duration: {scenario.duration_minutes}min")
        else:
            print("\n✅ BASELINE MODE (No anomalies)")
        
        print("="*70)
        
        start_time = time.time()
        cycle_count = 0
        simulated_start = self.start_time if self.simulate_time else None
        
        try:
            while True:
                cycle_count += 1
                
                # Update simulated time if enabled
                if simulated_start:
                    self.start_time = simulated_start + timedelta(seconds=cycle_count * self.interval)
                
                self.simulate_cycle()
                
                # Check duration
                if duration_hours:
                    if self.simulate_time:
                        # In simulated mode, check simulated hours
                        elapsed_hours = (cycle_count * self.interval) / 3600
                    else:
                        # Real time mode
                        elapsed_hours = (time.time() - start_time) / 3600
                    
                    if elapsed_hours >= duration_hours:
                        print(f"\n✅ Simulation completed: {duration_hours} hours ({cycle_count} cycles)")
                        break
                
                # Wait for next cycle
                if self.turbo_mode:
                    sleep_time = self.turbo_delay
                    if cycle_count % 10 == 0:  # Progress update every 10 cycles
                        print(f"⚡ Turbo cycle {cycle_count} completed (sleeping {sleep_time}s)...")
                else:
                    sleep_time = self.interval
                    print(f"\n⏳ Waiting {sleep_time} seconds until next cycle...")
                
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print(f"\n\n⚠️ Simulation stopped by user after {cycle_count} cycles")
            print("="*70)


def main():
    """Main entry point with test scenario selection."""
    parser = argparse.ArgumentParser(
        description='Enhanced Agricultural Sensor Simulator with Anomaly Injection'
    )
    parser.add_argument(
        '--api-url', 
        type=str, 
        default=SimulatorConfig.DEFAULT_API_URL,
        help=f'Django API base URL (default: {SimulatorConfig.DEFAULT_API_URL})'
    )
    parser.add_argument(
        '--plots', 
        type=int, 
        nargs='+', 
        default=SimulatorConfig.DEFAULT_PLOTS,
        help=f'Plot IDs to simulate (default: {SimulatorConfig.DEFAULT_PLOTS})'
    )
    parser.add_argument(
        '--interval', 
        type=int, 
        default=SimulatorConfig.DEFAULT_INTERVAL,
        help=f'Seconds between readings (default: {SimulatorConfig.DEFAULT_INTERVAL})'
    )
    parser.add_argument(
        '--duration', 
        type=float, 
        default=None,
        help='Simulation duration in hours (default: continuous)'
    )
    parser.add_argument(
        '--token', 
        type=str, 
        default=None,
        help='JWT authentication token'
    )
    parser.add_argument(
        '--scenario',
        type=str,
        choices=['baseline', 'irrigation_failure', 'sensor_malfunction', 
                'calibration_drift', 'full_suite', 'quick_test'],
        default='baseline',
        help='Test scenario to run (default: baseline - no anomalies)'
    )
    parser.add_argument(
        '--turbo',
        action='store_true',
        help='Turbo mode: minimal sleep between cycles for fast data generation'
    )
    parser.add_argument(
        '--turbo-delay',
        type=float,
        default=0.1,
        help='Delay between cycles in turbo mode (seconds, default: 0.1)'
    )
    parser.add_argument(
        '--simulate-time',
        action='store_true',
        help='Simulate historical time instead of using real time'
    )
    
    args = parser.parse_args()
    
    # Create anomaly manager based on scenario
    anomaly_manager = None
    
    if args.scenario == 'irrigation_failure':
        anomaly_manager = create_irrigation_failure_test()
        print("\n🧪 Test Scenario: IRRIGATION FAILURE")
        
    elif args.scenario == 'sensor_malfunction':
        anomaly_manager = create_sensor_malfunction_test()
        print("\n🧪 Test Scenario: SENSOR MALFUNCTION")
        
    elif args.scenario == 'calibration_drift':
        anomaly_manager = create_calibration_drift_test()
        print("\n🧪 Test Scenario: CALIBRATION DRIFT")
        
    elif args.scenario == 'full_suite':
        anomaly_manager = create_full_test_suite()
        print("\n🧪 Test Scenario: FULL TEST SUITE (All anomalies)")
        
    elif args.scenario == 'quick_test':
        anomaly_manager = create_quick_test()
        print("\n🧪 Test Scenario: QUICK TEST (Rapid validation)")
    
    else:
        print("\n✅ Running in BASELINE mode (no anomalies)")
    
    # Create and configure simulator
    simulator = SensorSimulator(
        api_url=args.api_url,
        plot_ids=args.plots,
        interval=args.interval,
        anomaly_manager=anomaly_manager
    )
    
    # Apply turbo mode settings
    if args.turbo:
        print(f"\n⚡ TURBO MODE ACTIVATED")
        print(f"   Sleep delay: {args.turbo_delay}s (instead of {args.interval}s)")
        simulator.turbo_mode = True
        simulator.turbo_delay = args.turbo_delay
    
    if args.simulate_time:
        print("   Using simulated historical time")
        simulator.simulate_time = True
    
    if args.token:
        simulator.set_auth_token(args.token)
    
    # Run simulation
    simulator.run(duration_hours=args.duration)


if __name__ == '__main__':
    main()