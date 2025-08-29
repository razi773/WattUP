# -*- coding: utf-8 -*-
"""
Module documentation
"""
from django.db import models
from django.utils import timezone
class XGBoostPrediction(models.Model):
    """Modèle pour stocker les prédictions XGBoost"""
    date = models.DateField(verbose_name="Date de prédiction")
    prediction_value = models.FloatField(verbose_name="Valeur prédite (kWh)")
    confidence = models.FloatField(verbose_name="Niveau de confiance", default=0.95)
    model_version = models.CharField(max_length=50, default="XGBoost_v1.0")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")
    class Meta:
        verbose_name = "Prédiction XGBoost"
        verbose_name_plural = "Prédictions XGBoost"
        ordering = ['date']
        unique_together = ['date', 'model_version']  
    def __str__(self):
        return f"Prédiction {self.date}: {self.prediction_value:.2f} kWh"
class PredictionBatch(models.Model):
    """Modèle pour grouper les prédictions par lot"""
    batch_id = models.CharField(max_length=100, unique=True, verbose_name="ID du lot")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    total_predictions = models.IntegerField(default=0, verbose_name="Nombre de prédictions")
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'En attente'),
            ('COMPLETED', 'Terminé'),
            ('FAILED', 'Échoué')
        ],
        default='PENDING',
        verbose_name="Statut"
    )
    class Meta:
        verbose_name = "Lot de prédictions"
        verbose_name_plural = "Lots de prédictions"
        ordering = ['-created_at']
    def __str__(self):
        return f"Lot {self.batch_id} - {self.total_predictions} prédictions"