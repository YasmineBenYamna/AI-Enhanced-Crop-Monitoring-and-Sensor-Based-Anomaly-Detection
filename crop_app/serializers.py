# ===================================================================
# serializers.py - COMPLETE WITH COMMENTS AND USER AUTHENTICATION
# ===================================================================

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import FarmProfile, FieldPlot, SensorReading, AnomalyEvent, AgentRecommendation


# ===================================================================
# USER SERIALIZER
# ===================================================================

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for Django User model
    - Returns user info with role (farmer/admin/superadmin)
    - Used in responses to show who owns farms
    """
    # Computed field to show user's role based on permissions
    role = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'role']
        read_only_fields = ['id', 'is_staff']  # Don't allow changing these via API
    
    def get_role(self, obj):
        """
        Determine user role based on Django permissions
        - Superuser = can do everything in Django admin
        - Staff = admin in our app (can see all farms)
        - Regular = farmer (can only see their own farms)
        """
        if obj.is_superuser:
            return 'superadmin'
        elif obj.is_staff:
            return 'admin'
        return 'farmer'


# ===================================================================
# FARM PROFILE SERIALIZER
# ===================================================================

class FarmProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for FarmProfile model
    - Includes owner information (username, email)
    - Shows how many plots belong to this farm
    - Auto-assigns owner for regular users (security)
    """
    # Read-only fields to show owner details without exposing full User object
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    
    # Computed field showing number of plots in this farm
    plot_count = serializers.IntegerField(source='plots.count', read_only=True)
    
    class Meta:
        model = FarmProfile
        fields = '__all__'  # All fields from model
        # OR explicitly: fields = ['id', 'owner', 'owner_username', 'owner_email', 
        #                           'location', 'size', 'crop_type', 'plot_count', 
        #                           'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """
        Override create to auto-assign owner for regular users
        - Regular users (farmers): owner = current logged-in user
        - Admins: can manually assign owner to any user
        
        SECURITY: Prevents regular users from creating farms for other users
        """
        request = self.context.get('request')
        
        # If regular user (not admin), force owner to be themselves
        if request and not request.user.is_staff:
            validated_data['owner'] = request.user
        
        return super().create(validated_data)


# ===================================================================
# FIELD PLOT SERIALIZER
# ===================================================================

class FieldPlotSerializer(serializers.ModelSerializer):
    """
    Serializer for FieldPlot model
    - Shows which farm this plot belongs to
    - Shows farm owner's username
    - Validates user can only create plots on their own farms
    """
    # Show the farm owner's username (useful for display)
    farm_owner = serializers.CharField(source='farm.owner.username', read_only=True)

    class Meta:
        model = FieldPlot
        fields = ['id', 'farm', 'farm_owner', 'crop_variety', 'plot_name', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_farm(self, value):
        """
        Validate that user can only create plots on their own farms
        - Admins: can create plots on any farm
        - Regular users: can only create plots on farms they own
        
        SECURITY: Prevents users from adding plots to other people's farms
        """
        request = self.context.get('request')
        
        # If regular user, check they own the farm
        if request and not request.user.is_staff:
            if value.owner != request.user:
                raise serializers.ValidationError(
                    "You can only create plots on your own farms."
                )
        
        return value


# ===================================================================
# SENSOR READING SERIALIZER
# ===================================================================

class SensorReadingSerializer(serializers.ModelSerializer):
    """
    Serializer for SensorReading model
    - Used for data ingestion from simulator
    - Validates sensor type and value ranges
    - Shows plot name for readability
    """
    # Allow posting with plot_id instead of nested plot object
    #plot = serializers.IntegerField(write_only=True)
    
    # Show plot name in responses (easier to read than just ID)
    plot_name = serializers.CharField(source='plot.plot_name', read_only=True)

    class Meta:
        model = SensorReading
        fields = ['id', 'timestamp', 'plot', 'plot_name', 
                  'sensor_type', 'value', 'source']
        read_only_fields = ['id','timestamp']  # Auto-set by database

    def validate_sensor_type(self, value):
        """
        Validate sensor type is one of the allowed types
        - Must match choices in model (moisture, temperature, humidity)
        """
        valid_types = ['moisture', 'temperature', 'humidity']
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid sensor type. Must be one of {valid_types}"
            )
        return value

    def validate_value(self, value):
        """
        Validate sensor values are within reasonable ranges
        - Prevents garbage data from simulator or malformed requests
        - Ranges based on project specifications (Table 1)
        
        Moisture: 0-100%
        Temperature: -50 to 60°C
        Humidity: 0-100%
        """
        sensor_type = self.initial_data.get('sensor_type')
        
        # Validate based on sensor type
        if sensor_type == 'moisture':
            if not (0 <= value <= 100):
                raise serializers.ValidationError(
                    "Moisture must be between 0-100%"
                )
        elif sensor_type == 'temperature':
            if not (-50 <= value <= 60):
                raise serializers.ValidationError(
                    "Temperature must be between -50 to 60°C"
                )
        elif sensor_type == 'humidity':
            if not (0 <= value <= 100):
                raise serializers.ValidationError(
                    "Humidity must be between 0-100%"
                )
        else:
            # Fallback for unknown sensor types
            if value < 0 or value > 200:
                raise serializers.ValidationError(
                    "Sensor value out of reasonable range (0-200)"
                )
        
        return value


# ===================================================================
# AGENT RECOMMENDATION SERIALIZER
# ===================================================================

class AgentRecommendationSerializer(serializers.ModelSerializer):
    """
    Serializer for AgentRecommendation model
    - AI agent's recommended actions for anomalies
    - Includes human-readable explanation
    - OneToOne relationship with AnomalyEvent
    """
    class Meta:
        model = AgentRecommendation
        fields = ['id', 'timestamp', 'anomaly_event', 'recommended_action',
                  'explanation_text', 'confidence']
        read_only_fields = ['timestamp']


# ===================================================================
# ANOMALY EVENT SERIALIZER
# ===================================================================

class AnomalyEventSerializer(serializers.ModelSerializer):
    """
    Serializer for AnomalyEvent model
    - ML-detected anomalies in sensor data
    - Includes nested plot information
    - Includes recommendation from AI agent (if exists)
    """
    # Nested serializer to show full plot details
    plot_info = FieldPlotSerializer(source='plot', read_only=True)
    
    # Show farm owner username (useful for admin dashboard)
    farm_owner = serializers.CharField(source='plot.farm.owner.username', read_only=True)
    
    # OneToOne relationship: each anomaly has one recommendation
    recommendation = AgentRecommendationSerializer(read_only=True)

    class Meta:
        model = AnomalyEvent
        fields = ['id', 'timestamp', 'plot', 'plot_info', 'farm_owner',
                  'anomaly_type', 'severity', 'model_confidence', 'recommendation']
        read_only_fields = ['timestamp']


# ===================================================================
# USAGE NOTES
# ===================================================================
"""
HOW TO USE THESE SERIALIZERS:

1. POST /api/farms/ (Create farm)
   {
       "location": "North Field",
       "size": 50.5,
       "crop_type": "wheat"
   }
   # owner is auto-assigned to current user (if not admin)

2. POST /api/plots/ (Create plot)
   {
       "farm": 1,
       "crop_variety": "Winter Wheat",
       "plot_name": "Plot A"
   }
   # Validates user owns farm #1

3. POST /api/sensor-readings/ (Ingest data)
   {
       "plot_id": 1,
       "sensor_type": "moisture",
       "value": 65.5,
       "source": "simulator"
   }
   # Validates value is 0-100 for moisture

4. GET /api/anomalies/
   # Returns anomalies with plot_info and recommendation nested

SECURITY:
- All endpoints require authentication (IsAuthenticated)
- Regular users only see their own data (filtered in views)
- Admins see all data
- Validation prevents users from accessing/creating data they shouldn't
"""