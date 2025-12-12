"""
Fast Historical Data Generator
Generates days/weeks of sensor data in seconds without real-time delays.
Usage: python fast_data_generator.py --days 7 --scenario baseline
"""

import requests
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


class FastDataGenerator:
    """Generate historical sensor data rapidly for training/testing."""
    
    def __init__(self, api_url: str, plot_ids: List[int], 
                 interval_seconds: int = 300, anomaly_manager: AnomalyManager = None):
        self.api_url = api_url
        self.plot_ids = plot_ids
        self.interval_seconds = interval_seconds
        self.anomaly_manager = anomaly_manager
        self.auth_token = None
        self.config = SimulatorConfig
        self.baseline_params = self.config.BASELINE_PARAMS
        
    def set_auth_token(self, token: str):
        self.auth_token = token
    
    def get_time_of_day(self, timestamp: datetime) -> float:
        return timestamp.hour + timestamp.minute / 60.0
    
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
        humidity = max(20.0, min(95.0, humidity))
        return round(humidity, 2)
    
    def generate_moisture_series(self, plot_id: int, num_readings: int, 
                                 start_time: datetime) -> List[tuple]:
        """Generate a complete moisture series with irrigation cycles."""
        params = self.baseline_params['moisture']
        moisture_values = []
        current_moisture = params['mean']
        last_irrigation = start_time
        
        for i in range(num_readings):
            current_time = start_time + timedelta(seconds=i * self.interval_seconds)
            hours_since_irrigation = (current_time - last_irrigation).total_seconds() / 3600
            
            # Check irrigation
            irrigation_interval = (
                self.config.IRRIGATION_INTERVAL_HOURS + 
                np.random.uniform(
                    -self.config.IRRIGATION_VARIANCE_HOURS,
                    self.config.IRRIGATION_VARIANCE_HOURS
                )
            )
            
            if hours_since_irrigation >= irrigation_interval:
                current_moisture += params['irrigation_boost']
                last_irrigation = current_time
            
            # Decay
            decay = params['decay_rate'] * (self.interval_seconds / 3600)
            current_moisture -= decay
            current_moisture += np.random.normal(0, params['noise_std'])
            current_moisture = max(30.0, min(80.0, current_moisture))
            
            moisture_values.append((current_time, round(current_moisture, 2)))
        
        return moisture_values
    
    def apply_anomalies(self, sensor_type: str, normal_value: float, 
                        hours_since_start: float) -> float:
        """Apply anomaly modifications based on time."""
        if self.anomaly_manager:
            # Update anomaly manager to current simulation time
            self.anomaly_manager.hours_elapsed = hours_since_start
            return self.anomaly_manager.modify_reading(sensor_type, normal_value)
        return normal_value
    
    def send_batch(self, readings: List[Dict]) -> bool:
        """Send batch of readings to API."""
        headers = {'Content-Type': 'application/json'}
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        try:
            # Try bulk endpoint first
            response = requests.post(
                f'{self.api_url}/sensor-readings/bulk/',
                json={'readings': readings},
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return True
            
            # Fallback: send individually
            success_count = 0
            for reading in readings:
                try:
                    resp = requests.post(
                        f'{self.api_url}/sensor-readings/',
                        json=reading,
                        headers=headers,
                        timeout=10
                    )
                    if resp.status_code in [200, 201]:
                        success_count += 1
                except:
                    continue
            
            return success_count > len(readings) * 0.8  # 80% success rate
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Batch send error: {e}")
            return False
    
    def generate_historical_data(self, days: float, batch_size: int = 100):
        """Generate historical data for specified number of days."""
        start_time = datetime.now() - timedelta(days=days)
        end_time = datetime.now()
        
        total_readings = int((days * 24 * 3600) / self.interval_seconds)
        readings_per_plot = total_readings // len(self.plot_ids)
        
        print("\n" + "="*70)
        print("🚀 FAST HISTORICAL DATA GENERATOR")
        print("="*70)
        print(f"API URL: {self.api_url}")
        print(f"Plot IDs: {self.plot_ids}")
        print(f"Time Range: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"Duration: {days} days ({days * 24:.1f} hours)")
        print(f"Interval: {self.interval_seconds}s ({self.interval_seconds/60:.1f} min)")
        print(f"Total Readings: {total_readings * len(self.plot_ids):,} ({total_readings:,} per plot)")
        print(f"Batch Size: {batch_size}")
        
        if self.anomaly_manager:
            print("\n🔬 ANOMALY INJECTION ENABLED")
            for scenario in self.anomaly_manager.scenarios:
                print(f"   • {scenario.name}: {scenario.start_hour}h → {scenario.start_hour + scenario.duration_minutes/60:.1f}h")
        else:
            print("\n✅ BASELINE MODE (No anomalies)")
        
        print("="*70)
        
        # Pre-generate moisture series for all plots
        print("\n📊 Pre-generating moisture cycles...")
        moisture_series = {}
        for plot_id in self.plot_ids:
            moisture_series[plot_id] = self.generate_moisture_series(
                plot_id, total_readings, start_time
            )
        print("✅ Moisture series generated")
        
        # Generate all readings
        print(f"\n🔄 Generating {total_readings * len(self.plot_ids):,} readings...")
        all_readings = []
        
        for i in range(total_readings):
            current_time = start_time + timedelta(seconds=i * self.interval_seconds)
            time_of_day = self.get_time_of_day(current_time)
            hours_since_start = (current_time - start_time).total_seconds() / 3600
            
            # Update anomaly manager
            if self.anomaly_manager:
                self.anomaly_manager.hours_elapsed = hours_since_start
                self.anomaly_manager.update()
            
            for plot_id in self.plot_ids:
                # Generate base values
                temp = self.generate_temperature(time_of_day)
                humidity = self.generate_humidity(temp, time_of_day)
                moisture = moisture_series[plot_id][i][1]
                
                # Apply anomalies
                temp = self.apply_anomalies('temperature', temp, hours_since_start)
                humidity = self.apply_anomalies('humidity', humidity, hours_since_start)
                moisture = self.apply_anomalies('moisture', moisture, hours_since_start)
                
                # Create readings
                for sensor_type, value in [
                    ('temperature', temp),
                    ('humidity', humidity),
                    ('moisture', moisture)
                ]:
                    all_readings.append({
                        'plot': plot_id,
                        'sensor_type': sensor_type,
                        'value': value,
                        'timestamp': current_time.isoformat(),
                        'source': 'fast_generator'
                    })
            
            # Progress indicator
            if (i + 1) % 100 == 0:
                progress = ((i + 1) / total_readings) * 100
                print(f"   Progress: {progress:.1f}% ({i+1:,}/{total_readings:,} cycles)", end='\r')
        
        print(f"\n✅ Generated {len(all_readings):,} readings")
        
        # Send in batches
        print(f"\n📤 Sending data in batches of {batch_size}...")
        total_batches = (len(all_readings) + batch_size - 1) // batch_size
        success_count = 0
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(all_readings))
            batch = all_readings[start_idx:end_idx]
            
            if self.send_batch(batch):
                success_count += 1
            
            progress = ((batch_num + 1) / total_batches) * 100
            print(f"   Batch {batch_num + 1}/{total_batches} ({progress:.1f}%)", end='\r')
        
        print(f"\n✅ Completed! {success_count}/{total_batches} batches sent successfully")
        print(f"📊 Data generation time span: {days} days compressed to seconds!")
        print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description='Fast Historical Data Generator for ML Training'
    )
    parser.add_argument(
        '--api-url',
        type=str,
        default=SimulatorConfig.DEFAULT_API_URL,
        help='Django API base URL'
    )
    parser.add_argument(
        '--plots',
        type=int,
        nargs='+',
        default=SimulatorConfig.DEFAULT_PLOTS,
        help='Plot IDs to generate data for'
    )
    parser.add_argument(
        '--days',
        type=float,
        default=7,
        help='Number of days of historical data to generate (default: 7)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=SimulatorConfig.DEFAULT_INTERVAL,
        help='Seconds between readings (default: 300)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of readings per batch (default: 100)'
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
        help='Anomaly scenario (default: baseline - no anomalies)'
    )
    
    args = parser.parse_args()
    
    # Create anomaly manager
    anomaly_manager = None
    if args.scenario == 'irrigation_failure':
        anomaly_manager = create_irrigation_failure_test()
    elif args.scenario == 'sensor_malfunction':
        anomaly_manager = create_sensor_malfunction_test()
    elif args.scenario == 'calibration_drift':
        anomaly_manager = create_calibration_drift_test()
    elif args.scenario == 'full_suite':
        anomaly_manager = create_full_test_suite()
    elif args.scenario == 'quick_test':
        anomaly_manager = create_quick_test()
    
    # Create generator
    generator = FastDataGenerator(
        api_url=args.api_url,
        plot_ids=args.plots,
        interval_seconds=args.interval,
        anomaly_manager=anomaly_manager
    )
    
    if args.token:
        generator.set_auth_token(args.token)
    
    # Generate data
    generator.generate_historical_data(
        days=args.days,
        batch_size=args.batch_size
    )


if __name__ == '__main__':
    main()