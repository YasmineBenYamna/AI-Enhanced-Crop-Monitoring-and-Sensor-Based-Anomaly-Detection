"""
Script pour créer des données de test dans la base de données
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crop_app_project.settings')
django.setup()

from django.contrib.auth.models import User
from crop_app.models import FarmProfile, FieldPlot, SensorReading, AnomalyEvent, AgentRecommendation
from django.utils import timezone
from datetime import timedelta

def create_test_data():
    """Crée des données de test complètes."""
    
    print("🌱 Création des données de test...")
    
    # 1. Créer un utilisateur
    user, created = User.objects.get_or_create(
        username='farmer1',
        defaults={
            'email': 'farmer1@example.com',
            'first_name': 'John',
            'last_name': 'Farmer'
        }
    )
    if created:
        user.set_password('password123')
        user.save()
        print(f"✅ User créé: {user.username}")
    else:
        print(f"ℹ️ User existe déjà: {user.username}")
    
    # 2. Créer une ferme
    farm, created = FarmProfile.objects.get_or_create(
        owner=user,
        defaults={
            'farm_name': 'Green Valley Farm',
            'location': 'California, USA',
            'size': 50.0,
            'crop_type': 'Mixed Vegetables'
        }
    )
    if created:
        print(f"✅ Farm créée: {farm.farm_name}")
    else:
        print(f"ℹ️ Farm existe déjà: {farm.farm_name}")
    
    # 3. Créer des parcelles
    plots_data = [
        {'plot_name': 'North Field', 'crop_variety': 'Tomatoes', 'area': 10.0},
        {'plot_name': 'South Field', 'crop_variety': 'Lettuce', 'area': 8.0},
        {'plot_name': 'East Field', 'crop_variety': 'Carrots', 'area': 12.0},
    ]
    
    plots = []
    for plot_data in plots_data:
        plot, created = FieldPlot.objects.get_or_create(
            farm=farm,
            plot_name=plot_data['plot_name'],
            defaults={
                'crop_variety': plot_data['crop_variety'],
                'area': plot_data['area']
            }
        )
        plots.append(plot)
        if created:
            print(f"✅ Plot créé: {plot.plot_name}")
        else:
            print(f"ℹ️ Plot existe déjà: {plot.plot_name}")
    
    # 4. Créer des lectures de capteurs
    print("\n📊 Création des lectures de capteurs...")
    now = timezone.now()
    
    for plot in plots:
        # Créer 20 lectures sur les dernières 24h
        for i in range(20):
            timestamp = now - timedelta(hours=24-i)
            
            # Simuler une baisse d'humidité progressive
            base_moisture = 65.0
            moisture = base_moisture - (i * 1.5)  # Baisse progressive
            
            SensorReading.objects.get_or_create(
                plot=plot,
                timestamp=timestamp,
                defaults={
                    'soil_moisture': max(30.0, moisture),
                    'air_temperature': 25.0 + (i * 0.3),
                    'air_humidity': 60.0 - (i * 0.5),
                    'soil_temperature': 22.0,
                    'light_intensity': 500.0
                }
            )
    
    total_readings = SensorReading.objects.count()
    print(f"✅ {total_readings} lectures de capteurs créées")
    
    # 5. Créer des anomalies
    print("\n⚠️ Création des anomalies...")
    
    anomalies_data = [
        {
            'plot': plots[0],
            'anomaly_type': 'moisture_anomaly',
            'severity': 'HIGH',
            'model_confidence': 0.85,
            'description': 'Rapid moisture drop detected'
        },
        {
            'plot': plots[0],
            'anomaly_type': 'temperature_anomaly',
            'severity': 'CRITICAL',
            'model_confidence': 0.92,
            'description': 'Critical temperature levels'
        },
        {
            'plot': plots[1],
            'anomaly_type': 'humidity_anomaly',
            'severity': 'MEDIUM',
            'model_confidence': 0.78,
            'description': 'High humidity detected'
        },
        {
            'plot': plots[2],
            'anomaly_type': 'moisture_anomaly',
            'severity': 'HIGH',
            'model_confidence': 0.88,
            'description': 'Soil moisture below threshold'
        }
    ]
    
    for anomaly_data in anomalies_data:
        anomaly, created = AnomalyEvent.objects.get_or_create(
            plot=anomaly_data['plot'],
            anomaly_type=anomaly_data['anomaly_type'],
            timestamp__gte=now - timedelta(hours=2),
            defaults={
                'severity': anomaly_data['severity'],
                'model_confidence': anomaly_data['model_confidence'],
                'timestamp': now - timedelta(minutes=30)
            }
        )
        
        if created:
            print(f"✅ Anomalie créée: {anomaly.anomaly_type} sur {anomaly.plot.plot_name}")
            
            # Vérifier si recommandation auto-générée
            if hasattr(anomaly, 'recommendation'):
                print(f"   ✅ Recommandation auto-générée par signal!")
            else:
                print(f"   ℹ️ Pas de recommandation auto-générée")
        else:
            print(f"ℹ️ Anomalie existe déjà: {anomaly.anomaly_type}")
    
    
    # 6. Afficher les statistiques finales
    print("\n" + "="*50)
    print("📊 STATISTIQUES FINALES")
    print("="*50)
    print(f"👤 Users: {User.objects.count()}")
    print(f"🌾 Farms: {FarmProfile.objects.count()}")
    print(f"📍 Plots: {FieldPlot.objects.count()}")
    print(f"📊 Sensor Readings: {SensorReading.objects.count()}")
    print(f"⚠️ Anomalies: {AnomalyEvent.objects.count()}")
    print(f"🤖 Recommendations: {AgentRecommendation.objects.count()}")
    print("="*50)
    
    print("\n✅ Données de test créées avec succès!")
    print("🔍 Vérifiez maintenant dans pgAdmin!")

if __name__ == '__main__':
    create_test_data()