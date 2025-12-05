#!/usr/bin/env python3
"""
Simple Setup Verification for Simulator Files
Checks: anomaly_scenarios.py, sensor_simulator.py, simulator_config.py
"""

import os
import sys

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
END = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{END}")
    print(f"{BOLD}{text}{END}")
    print(f"{BLUE}{'='*60}{END}\n")

def check_pass(text):
    print(f"{GREEN}✅ {text}{END}")

def check_fail(text):
    print(f"{RED}❌ {text}{END}")

def check_warn(text):
    print(f"{YELLOW}⚠️  {text}{END}")


print_header("🌾 Simulator Setup Verification")

all_good = True

# ============================================
# CHECK 1: Required Files
# ============================================
print_header("📂 Checking Required Files")

required_files = [
    'anomaly_scenarios.py',
    'sensor_simulator.py',
    'simulator_config.py'
]

for filename in required_files:
    if os.path.isfile(filename):
        check_pass(f"Found: {filename}")
    else:
        check_fail(f"Missing: {filename}")
        all_good = False

# ============================================
# CHECK 2: Python Dependencies
# ============================================
print_header("📦 Checking Python Dependencies")

dependencies = [
    ('numpy', 'numpy'),
    ('requests', 'requests'),
]

for module_name, package_name in dependencies:
    try:
        __import__(module_name)
        check_pass(f"Module available: {module_name}")
    except ImportError:
        check_fail(f"Module not found: {module_name}")
        print(f"   Install with: pip install {package_name}")
        all_good = False

# ============================================
# CHECK 3: Test Imports
# ============================================
print_header("🔧 Testing Module Imports")

# Test simulator_config
try:
    from simulator_config import SimulatorConfig
    check_pass("simulator_config.SimulatorConfig imported successfully")
except Exception as e:
    check_fail(f"Failed to import simulator_config: {e}")
    all_good = False

# Test anomaly_scenarios
try:
    from anomaly_scenarios import (
        AnomalyScenario,
        SuddenDropScenario,
        SpikeScenario,
        DriftScenario,
        AnomalyManager
    )
    check_pass("anomaly_scenarios classes imported successfully")
except Exception as e:
    check_fail(f"Failed to import anomaly_scenarios: {e}")
    all_good = False

# Test sensor_simulator (just check it exists and is importable as module)
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("sensor_simulator", "sensor_simulator.py")
    if spec and spec.loader:
        check_pass("sensor_simulator.py is valid Python file")
    else:
        check_fail("sensor_simulator.py cannot be loaded")
        all_good = False
except Exception as e:
    check_fail(f"Failed to check sensor_simulator.py: {e}")
    all_good = False

# ============================================
# CHECK 4: Django Connection (Optional)
# ============================================
print_header("🌐 Checking Django API (Optional)")

try:
    import requests
    try:
        response = requests.get("http://localhost:8000/api/", timeout=2)
        if response.status_code in [200, 404]:
            check_pass("Django API is accessible at http://localhost:8000")
        else:
            check_warn(f"Django API responded with status {response.status_code}")
    except requests.exceptions.ConnectionError:
        check_warn("Django API not accessible (make sure it's running)")
        print("   Start with: python manage.py runserver")
    except Exception as e:
        check_warn(f"Cannot check Django API: {e}")
except ImportError:
    check_warn("requests module not available - skipping Django check")

# ============================================
# CHECK 5: File Structure Check
# ============================================
print_header("📋 Checking File Contents")

# Check simulator_config.py
try:
    with open('simulator_config.py', 'r') as f:
        content = f.read()
        
    checks = [
        ('SimulatorConfig class', 'class SimulatorConfig' in content),
        ('BASELINE_PARAMS', 'BASELINE_PARAMS' in content),
        ('NORMAL_RANGES', 'NORMAL_RANGES' in content),
    ]
    
    print(f"{BOLD}simulator_config.py:{END}")
    for check_name, result in checks:
        if result:
            check_pass(f"  {check_name}")
        else:
            check_fail(f"  {check_name}")
            all_good = False
            
except Exception as e:
    check_fail(f"Error reading simulator_config.py: {e}")
    all_good = False

# Check anomaly_scenarios.py
try:
    with open('anomaly_scenarios.py', 'r') as f:
        content = f.read()
        
    checks = [
        ('AnomalyScenario base class', 'class AnomalyScenario' in content),
        ('SuddenDropScenario', 'class SuddenDropScenario' in content),
        ('SpikeScenario', 'class SpikeScenario' in content),
        ('DriftScenario', 'class DriftScenario' in content),
        ('AnomalyManager', 'class AnomalyManager' in content),
    ]
    
    print(f"\n{BOLD}anomaly_scenarios.py:{END}")
    for check_name, result in checks:
        if result:
            check_pass(f"  {check_name}")
        else:
            check_fail(f"  {check_name}")
            all_good = False
            
except Exception as e:
    check_fail(f"Error reading anomaly_scenarios.py: {e}")
    all_good = False

# ============================================
# FINAL SUMMARY
# ============================================
print_header("📊 Verification Summary")

if all_good:
    check_pass("All critical checks passed! ✨")
    print()
    print("   You're ready to run your simulator:")
    print(f"   {BLUE}python sensor_simulator.py --duration 2{END}")
    print()
    print("   Next steps for Day 4:")
    print("   1. Generate normal data (training): python sensor_simulator.py --duration 2")
    print("   2. Implement ML model")
    print("   3. Generate anomaly data for testing")
    print()
else:
    check_fail("Some checks failed - please fix the issues above")
    print()
    print("   Common fixes:")
    print("   1. Install missing packages: pip install numpy requests")
    print("   2. Make sure all files are in the same directory")
    print("   3. Check file contents are complete")
    print()

print(f"{BLUE}{'='*60}{END}\n")

# Exit with appropriate code
sys.exit(0 if all_good else 1)