"""
Test Script for AI Agent
Run this from the same directory as manage.py
"""

import os
import sys
import django

# Add current directory to Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crop_app_project.settings')
django.setup()

from crop_app.models import FarmProfile, FieldPlot, SensorReading, AnomalyEvent, AgentRecommendation
from ai_agent.agent_service import get_agent_service
from django.contrib.auth.models import User
from datetime import datetime


def create_test_data():
    """Create test farm, plot, and sensor data."""
    print("📦 Creating test data...")
    
    # Create user
    user, _ = User.objects.get_or_create(
        username='test_farmer',
        defaults={'email': 'farmer@test.com'}
    )
    
    # Create farm
    farm, _ = FarmProfile.objects.get_or_create(
        owner=user,
        location='Test Farm',
        defaults={
            'size': 10.0,
            'crop_type': 'Wheat'
        }
    )
    
    # Create plot
    plot, _ = FieldPlot.objects.get_or_create(
        farm=farm,
        crop_variety='Winter Wheat',
        defaults={'plot_name': 'Test Plot 1'}
    )
    
    print(f"✅ Created farm {farm.id}, plot {plot.id}")
    return plot


def test_moisture_drop_anomaly(plot):
    """Test Rule 1: Sudden moisture drop."""
    print("\n🧪 Test 1: Sudden Moisture Drop (Irrigation Failure)")
    print("=" * 60)
    
    # Create sensor readings showing sudden drop
    import time
    readings = []
    for val in [65.0, 62.0, 58.0, 50.0]:  # Gradual then sudden drop
        reading = SensorReading.objects.create(
            plot=plot, 
            sensor_type='moisture', 
            value=val
        )
        readings.append(reading)
        time.sleep(0.1)  # Small delay to ensure different timestamps
    
    # Create anomaly manually (this will trigger the signal)
    anomaly = AnomalyEvent.objects.create(
        plot=plot,
        anomaly_type='moisture_anomaly',  # Matches your ML module
        severity='high',  # From your severity mapping
        model_confidence=0.85,
        sensor_reading=readings[-1]  # Link to the reading that triggered it
    )
    
    print(f"Created anomaly: {anomaly.id}")
    
    # Check if recommendation was auto-created by signal
    if hasattr(anomaly, 'recommendation'):
        rec = anomaly.recommendation
        print(f"\n✅ Recommendation auto-created by signal!")
        print(f"   ID: {rec.id}")
        print(f"   Action: {rec.recommended_action}")
        print(f"   Confidence: {rec.confidence}")
        print(f"   Explanation: {rec.explanation_text[:100]}...")
    else:
        print("❌ No recommendation created - signals may not be working")


def test_high_temperature(plot):
    """Test Rule 2: High temperature (heat stress)."""
    print("\n🧪 Test 2: High Temperature (Heat Stress)")
    print("=" * 60)
    
    reading = SensorReading.objects.create(
        plot=plot,
        sensor_type='temperature',
        value=35.0  # Above critical threshold
    )
    
    anomaly = AnomalyEvent.objects.create(
        plot=plot,
        anomaly_type='temperature_anomaly',
        severity='high',
        model_confidence=0.92,
        sensor_reading=reading
    )
    
    if hasattr(anomaly, 'recommendation'):
        rec = anomaly.recommendation
        print(f"✅ Action: {rec.recommended_action}")
        print(f"   Explanation: {rec.explanation_text[:100]}...")
    else:
        print("❌ No recommendation created")


def test_low_confidence_anomaly(plot):
    """Test Rule 3: Low confidence anomaly."""
    print("\n🧪 Test 3: Low Confidence Anomaly")
    print("=" * 60)
    
    reading = SensorReading.objects.create(
        plot=plot,
        sensor_type='humidity',
        value=50.0
    )
    
    anomaly = AnomalyEvent.objects.create(
        plot=plot,
        anomaly_type='humidity_anomaly',
        severity='low',
        model_confidence=0.45,  # Low confidence
        sensor_reading=reading
    )
    
    if hasattr(anomaly, 'recommendation'):
        rec = anomaly.recommendation
        print(f"✅ Action: {rec.recommended_action}")
        print(f"   Confidence: {rec.confidence}")
    else:
        print("❌ No recommendation created")


def test_manual_processing():
    """Test manual agent processing."""
    print("\n🧪 Test 4: Manual Agent Processing")
    print("=" * 60)
    
    agent_service = get_agent_service()
    
    # Get pending anomalies
    pending = agent_service.get_pending_anomalies()
    print(f"Found {pending.count()} pending anomalies")
    
    # Process them
    result = agent_service.process_pending_anomalies()
    print(f"Processed: {result['processed']}")
    print(f"Failed: {result['failed']}")


def view_all_recommendations():
    """Display all recommendations."""
    print("\n📊 All Recommendations Summary")
    print("=" * 60)
    
    recommendations = AgentRecommendation.objects.select_related(
        'anomaly_event', 'anomaly_event__plot'
    ).order_by('-timestamp')[:10]
    
    for rec in recommendations:
        print(f"\n🔔 Recommendation #{rec.id}")
        print(f"   Plot: {rec.anomaly_event.plot.plot_name or rec.anomaly_event.plot.id}")
        print(f"   Anomaly: {rec.anomaly_event.anomaly_type} ({rec.anomaly_event.severity})")
        print(f"   Action: {rec.recommended_action}")
        print(f"   Confidence: {rec.confidence:.2f}")
        print(f"   Time: {rec.timestamp}")


def main():
    """Run all tests."""
    print("🚀 AI Agent Test Suite")
    print("=" * 60)
    
    # Create test data
    plot = create_test_data()
    
    # Run tests
    test_moisture_drop_anomaly(plot)
    test_high_temperature(plot)
    test_low_confidence_anomaly(plot)
    test_manual_processing()
    
    # View results
    view_all_recommendations()
    
    print("\n✅ All tests completed!")


if __name__ == '__main__':
    main()