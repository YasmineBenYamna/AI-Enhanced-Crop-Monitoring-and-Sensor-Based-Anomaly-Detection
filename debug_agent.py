"""
Comprehensive Debugging Script for AI Agent
Run this to diagnose the issue: python debug_agent.py
"""

import os
import sys
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crop_app_project.settings')
django.setup()

from crop_app.models import AnomalyEvent, SensorReading, AgentRecommendation, FieldPlot
from ai_agent.agent_service import get_agent_service
from django.db.models.signals import post_save


def check_signal_registration():
    """Check if the signal is properly registered."""
    print("\n" + "="*70)
    print("🔍 STEP 1: Checking Signal Registration")
    print("="*70)
    
    # Get all receivers for AnomalyEvent post_save signal
    receivers = post_save._live_receivers(AnomalyEvent)
    
    print(f"Number of receivers registered: {len(receivers)}")
    
    for receiver in receivers:
        print(f"  ✓ Receiver: {receiver}")
    
    if len(receivers) == 0:
        print("\n❌ NO SIGNALS REGISTERED!")
        print("   Fix: Make sure signals.py is imported in apps.py")
        return False
    else:
        print("\n✅ Signals are registered")
        return True


def check_existing_anomalies():
    """Check existing anomalies and their sensor_reading links."""
    print("\n" + "="*70)
    print("🔍 STEP 2: Checking Existing Anomalies")
    print("="*70)
    
    anomalies = AnomalyEvent.objects.all().order_by('-timestamp')[:10]
    
    if anomalies.count() == 0:
        print("❌ No anomalies found in database")
        return False
    
    print(f"Found {anomalies.count()} recent anomalies\n")
    
    issues_found = False
    
    for anomaly in anomalies:
        print(f"📊 Anomaly #{anomaly.id}")
        print(f"   Type: {anomaly.anomaly_type}")
        print(f"   Severity: {anomaly.severity}")
        print(f"   Confidence: {anomaly.model_confidence}")
        print(f"   Timestamp: {anomaly.timestamp}")
        
        # Check sensor_reading link
        if anomaly.sensor_reading is None:
            print(f"   ⚠️  sensor_reading: NULL ← PROBLEM!")
            issues_found = True
        else:
            print(f"   ✓ sensor_reading: ID {anomaly.sensor_reading.id}")
            print(f"     - Type: {anomaly.sensor_reading.sensor_type}")
            print(f"     - Value: {anomaly.sensor_reading.value}")
        
        # Check recommendation
        if hasattr(anomaly, 'recommendation'):
            print(f"   ✓ recommendation: ID {anomaly.recommendation.id}")
        else:
            print(f"   ❌ recommendation: NOT CREATED ← PROBLEM!")
            issues_found = True
        
        print()
    
    if issues_found:
        print("⚠️  Issues found with anomaly data")
        return False
    else:
        print("✅ All anomalies look good")
        return True


def check_model_relationships():
    """Verify model relationships are correct."""
    print("\n" + "="*70)
    print("🔍 STEP 3: Checking Model Relationships")
    print("="*70)
    
    # Check if AnomalyEvent has sensor_reading field
    try:
        from crop_app.models import AnomalyEvent
        fields = [f.name for f in AnomalyEvent._meta.get_fields()]
        
        print("AnomalyEvent fields:")
        for field in fields:
            print(f"  - {field}")
        
        if 'sensor_reading' not in fields:
            print("\n❌ CRITICAL: 'sensor_reading' field NOT FOUND in AnomalyEvent model!")
            print("   Add this to your AnomalyEvent model:")
            print("   sensor_reading = models.ForeignKey(SensorReading, on_delete=models.SET_NULL, null=True, blank=True)")
            return False
        else:
            print("\n✅ sensor_reading field exists")
        
        # Check reverse relationship
        if 'recommendation' not in fields:
            print("⚠️  'recommendation' reverse relationship not found")
            print("   Check AgentRecommendation model has: anomaly_event = models.OneToOneField(...)")
        else:
            print("✅ recommendation relationship exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False


def test_manual_anomaly_creation():
    """Create a test anomaly manually and see if recommendation is created."""
    print("\n" + "="*70)
    print("🔍 STEP 4: Testing Manual Anomaly Creation")
    print("="*70)
    
    try:
        # Get or create a plot
        plot = FieldPlot.objects.first()
        if not plot:
            print("❌ No plots found. Create a plot first.")
            return False
        
        print(f"Using plot: {plot.id}")
        
        # Create a sensor reading
        sensor_reading = SensorReading.objects.create(
            plot=plot,
            sensor_type='moisture',
            value=35.0  # Low moisture
        )
        print(f"✓ Created sensor reading: ID {sensor_reading.id}, value={sensor_reading.value}")
        
        # Create anomaly (should trigger signal)
        print("\n🚨 Creating anomaly (signal should fire)...")
        anomaly = AnomalyEvent.objects.create(
            plot=plot,
            anomaly_type='moisture_anomaly',
            severity='high',
            model_confidence=0.87,
            sensor_reading=sensor_reading  # Link the reading!
        )
        print(f"✓ Created anomaly: ID {anomaly.id}")
        
        # Check if recommendation was created
        import time
        time.sleep(0.5)  # Give signal time to process
        
        if hasattr(anomaly, 'recommendation'):
            rec = anomaly.recommendation
            print(f"\n✅ SUCCESS! Recommendation auto-created by signal!")
            print(f"   ID: {rec.id}")
            print(f"   Action: {rec.recommended_action}")
            print(f"   Confidence: {rec.confidence}")
            print(f"   Explanation: {rec.explanation_text[:150]}...")
            return True
        else:
            print(f"\n❌ FAILURE! No recommendation created")
            print("   Checking if we can create manually...")
            
            # Try manual creation
            agent_service = get_agent_service()
            rec = agent_service.process_anomaly(anomaly)
            print(f"   ✓ Manual creation worked: ID {rec.id}")
            print(f"   This means signals are NOT working properly!")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_apps_config():
    """Check if apps.py is properly configured."""
    print("\n" + "="*70)
    print("🔍 STEP 5: Checking Apps Configuration")
    print("="*70)
    
    try:
        from django.apps import apps
        
        # Check if ai_agent app is registered
        if apps.is_installed('ai_agent'):
            print("✅ ai_agent app is installed")
            
            # Get the app config
            app_config = apps.get_app_config('ai_agent')
            print(f"   App config: {app_config.__class__.__name__}")
            
            # Check if it has ready() method
            if hasattr(app_config, 'ready'):
                print("   ✓ Has ready() method")
            else:
                print("   ⚠️  No ready() method - signals may not be imported!")
            
            return True
        else:
            print("❌ ai_agent app NOT installed in INSTALLED_APPS")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def suggest_fixes():
    """Provide fix suggestions based on findings."""
    print("\n" + "="*70)
    print("🔧 SUGGESTED FIXES")
    print("="*70)
    
    print("\n1️⃣ Ensure signals are registered:")
    print("   Create/update ai_agent/apps.py:")
    print("""
   from django.apps import AppConfig
   
   class AiAgentConfig(AppConfig):
       default_auto_field = 'django.db.models.BigAutoField'
       name = 'ai_agent'
       
       def ready(self):
           import ai_agent.signals  # This imports signals!
   """)
    
    print("\n2️⃣ Create/update ai_agent/__init__.py:")
    print("   default_app_config = 'ai_agent.apps.AiAgentConfig'")
    
    print("\n3️⃣ Ensure AnomalyEvent model has sensor_reading field:")
    print("""
   class AnomalyEvent(models.Model):
       # ... other fields ...
       sensor_reading = models.ForeignKey(
           SensorReading,
           on_delete=models.SET_NULL,
           null=True,
           blank=True,
           related_name='anomaly_events'
       )
   """)
    
    print("\n4️⃣ When ML module creates anomalies, ALWAYS link sensor_reading:")
    print("""
   # In your ML anomaly detection code:
   anomaly = AnomalyEvent.objects.create(
       plot=plot,
       anomaly_type='moisture_anomaly',
       severity='high',
       model_confidence=0.85,
       sensor_reading=the_sensor_reading  # ← Don't forget this!
   )
   """)
    
    print("\n5️⃣ Check INSTALLED_APPS in settings.py includes:")
    print("   'ai_agent.apps.AiAgentConfig',  # or just 'ai_agent'")


def main():
    """Run all diagnostic checks."""
    print("\n" + "="*70)
    print("🔬 AI AGENT DIAGNOSTIC TOOL")
    print("="*70)
    
    results = {
        'signals': check_signal_registration(),
        'apps': check_apps_config(),
        'models': check_model_relationships(),
        'anomalies': check_existing_anomalies(),
        'test': test_manual_anomaly_creation()
    }
    
    print("\n" + "="*70)
    print("📋 DIAGNOSTIC SUMMARY")
    print("="*70)
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {check}")
    
    if all(results.values()):
        print("\n🎉 Everything looks good!")
    else:
        print("\n⚠️  Issues found - see suggested fixes below")
        suggest_fixes()


if __name__ == '__main__':
    main()