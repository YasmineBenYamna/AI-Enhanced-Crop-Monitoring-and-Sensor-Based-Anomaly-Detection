from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


# -------------------- Enumerations/Choices --------------------

class SensorType(models.TextChoices):
    MOISTURE = "moisture", "Moisture"
    TEMPERATURE = "temperature", "Temperature"
    HUMIDITY = "humidity", "Humidity"


class SeverityLevel(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


# -------------------- Core Models --------------------

class FarmProfile(models.Model):
    owner = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    size = models.FloatField(help_text="Size in hectares", validators=[MinValueValidator(0)])
    crop_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'farm_profile'
        ordering = ['owner']
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['location']),
        ]
        verbose_name = 'Farm Profile'
        verbose_name_plural = 'Farm Profiles'


class FieldPlot(models.Model):
    crop_variety = models.CharField(max_length=100)
    plot_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Relationship between FieldPlot and FarmProfile [* - 1]
    farm = models.ForeignKey(
        FarmProfile,
        on_delete=models.CASCADE,
        related_name='plots'
    )

    class Meta:
        db_table = 'field_plot'
        ordering = ['id']
        indexes = [
            models.Index(fields=['crop_variety']),
            models.Index(fields=['farm']),
        ]
        verbose_name = 'Field Plot'
        verbose_name_plural = 'Field Plots'


class SensorReading(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    sensor_type = models.CharField(max_length=20, choices=SensorType.choices)
    value = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(200)])
    source = models.CharField(max_length=100, default="simulator")
    # Relationship between SensorReading and FieldPlot [* - 1]
    plot = models.ForeignKey(
        FieldPlot,
        on_delete=models.CASCADE,
        related_name='sensor_readings'
    )

    class Meta:
        db_table = 'sensor_reading'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['sensor_type']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['plot', 'timestamp']),
        ]
        verbose_name = 'Sensor Reading'
        verbose_name_plural = 'Sensor Readings'


class AnomalyEvent(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    anomaly_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=50, choices=SeverityLevel.choices)
    model_confidence = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    # Relationship between AnomalyEvent and FieldPlot [* - 1]
    plot = models.ForeignKey(
        FieldPlot,
        on_delete=models.CASCADE,
        related_name='anomalies'
    )

    class Meta:
        db_table = 'anomaly_event'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['severity']),
            models.Index(fields=['anomaly_type']),
            models.Index(fields=['plot', 'timestamp']),
        ]
        verbose_name = 'Anomaly Event'
        verbose_name_plural = 'Anomaly Events'


class AgentRecommendation(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    recommended_action = models.CharField(max_length=200)
    explanation_text = models.TextField()
    confidence = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    # Relationship between AgentRecommendation and AnomalyEvent [1 - 1]
    anomaly_event = models.OneToOneField(
        AnomalyEvent,
        on_delete=models.CASCADE,
        related_name='recommendation'  # Changed to singular!
    )

    class Meta:
        db_table = 'agent_recommendation'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['confidence']),
            models.Index(fields=['anomaly_event']),
        ]
        verbose_name = 'Agent Recommendation'
        verbose_name_plural = 'Agent Recommendations'
