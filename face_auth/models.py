# -*- coding: utf-8 -*-
"""
Module documentation
"""

from django.db import models
from django.utils import timezone

class FaceUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    face_encoding = models.BinaryField()  
    def __str__(self):
        return self.username

class UploadedImage(models.Model):
    """
    Modèle pour stocker les images uploadées et leurs prédictions
    """
    image = models.ImageField(upload_to="uploads/")
    result_label = models.CharField(max_length=20, blank=True, null=True)
    confidence = models.FloatField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user_session = models.CharField(max_length=100, blank=True, null=True)  # Pour associer à l'utilisateur
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Image Uploadée"
        verbose_name_plural = "Images Uploadées"
    
    def __str__(self):
        return f"Image {self.id} - {self.result_label} ({self.confidence:.2f}%)"
    
    @property
    def confidence_percentage(self):
        """Retourne la confiance en pourcentage"""
        return round(self.confidence * 100, 2) if self.confidence else 0
    
    @property
    def is_anomaly(self):
        """Vérifie si l'image est une anomalie"""
        return self.result_label == "anomaly"
