"""
Configuration for Sensor Simulator
Baseline parameters for normal sensor behavior only.
"""

from typing import Dict


class SimulatorConfig:
    """Configuration for sensor simulation parameters."""
    
    # API Configuration
    DEFAULT_API_URL = "http://localhost:8000/api"
    DEFAULT_PLOTS = [1, 2]
    DEFAULT_INTERVAL = 300  # 5 minutes in seconds
    
    # Sensor Normal Ranges (from project specification)
    NORMAL_RANGES = {
        'moisture': {
            'min': 45.0,
            'max': 75.0,
            'critical_low': 35.0,
            'critical_high': 80.0
        },
        'temperature': {
            'min': 18.0,
            'max': 28.0,
            'critical_low': 10.0,
            'critical_high': 32.0
        },
        'humidity': {
            'min': 45.0,
            'max': 75.0,
            'critical_low': 30.0,
            'critical_high': 85.0
        }
    }
    
    # Baseline simulation parameters
    BASELINE_PARAMS = {
        'moisture': {
            'mean': 60.0,                # Target moisture percentage
            'amplitude': 10.0,           # Daily variation amplitude
            'irrigation_boost': 15.0,    # Moisture increase after irrigation
            'decay_rate': 0.05,          # Hourly moisture loss rate (gradual decrease during day)
            'noise_std': 2.0             # Random noise
        },
        'temperature': {
            'mean': 23.0,                # Average temperature (°C)
            'amplitude': 8.0,            # Daily variation amplitude
            'peak_hour': 14,             # Hour of peak temperature (2 PM - afternoon peak)
            'noise_std': 1.5             # Random noise
        },
        'humidity': {
            'mean': 60.0,                # Average humidity (%)
            'amplitude': 15.0,           # Daily variation amplitude
            'temp_correlation': -0.6,    # Negative correlation with temperature (inverse)
            'noise_std': 3.0             # Random noise (some randomness)
        }
    }
    
    # Irrigation schedule (simulated every 12-24 hours)
    IRRIGATION_INTERVAL_HOURS = 18  # Base interval (middle of 12-24 range)
    IRRIGATION_VARIANCE_HOURS = 4   # Random variance (±4 hours = 14-22 hour range)


# Scenario 1: Soil Moisture Pattern
MOISTURE_SCENARIO = {
    'description': 'Soil moisture: gradual decrease during day, increase after irrigation (simulated every 12–24 hours)',
    'parameters': {
        'gradual_decrease': 'decay_rate: 0.05% per hour',
        'irrigation_cycle': '18 ± 4 hours (14-22 hour range)',
        'irrigation_boost': '+15% moisture increase',
        'baseline': '60% ± 10%'
    }
}

# Scenario 2: Temperature and Humidity Patterns
TEMP_HUMIDITY_SCENARIO = {
    'description': 'Temperature: diurnal cycle (lower at night, peak in afternoon). Humidity: inverse correlation with temperature, with some randomness',
    'temperature': {
        'pattern': 'Sinusoidal diurnal cycle',
        'night_low': '~15°C (lowest around 6 AM)',
        'afternoon_peak': '~31°C (peak at 2 PM)',
        'mean': '23°C',
        'amplitude': '8°C'
    },
    'humidity': {
        'pattern': 'Inverse correlation with temperature',
        'correlation_coefficient': -0.6,
        'mean': '60%',
        'amplitude': '15%',
        'randomness': 'noise_std: 3.0%'
    }
}


def print_scenarios():
    """Display the two baseline scenarios."""
    print("\n" + "=" * 80)
    print("BASELINE SENSOR SCENARIOS")
    print("=" * 80)
    
    print("\n" + "─" * 80)
    print("SCENARIO 1: Soil Moisture Pattern")
    print("─" * 80)
    print(f"Description: {MOISTURE_SCENARIO['description']}")
    print("\nParameters:")
    for key, value in MOISTURE_SCENARIO['parameters'].items():
        print(f"  • {key}: {value}")
    
    print("\n" + "─" * 80)
    print("SCENARIO 2: Temperature & Humidity Patterns")
    print("─" * 80)
    print(f"Description: {TEMP_HUMIDITY_SCENARIO['description']}")
    print("\nTemperature:")
    for key, value in TEMP_HUMIDITY_SCENARIO['temperature'].items():
        print(f"  • {key}: {value}")
    print("\nHumidity:")
    for key, value in TEMP_HUMIDITY_SCENARIO['humidity'].items():
        print(f"  • {key}: {value}")
    
    print("\n" + "=" * 80)
    print("These patterns are implemented in sensor_simulator.py")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    """Display scenarios when run directly."""
    print_scenarios()
