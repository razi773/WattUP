"""
Utilitaire pour la prédiction d'images avec le modèle Keras
"""
import os
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ImagePredictor:
    """
    Classe pour charger le modèle et faire des prédictions d'images
    """
    
    def __init__(self):
        self.model = None
        self.model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'best_model.keras')
        self.load_model()
    
    def load_model(self):
        """
        Charge le modèle Keras depuis le fichier
        """
        try:
            if os.path.exists(self.model_path):
                self.model = tf.keras.models.load_model(self.model_path)
                logger.info(f"✅ Modèle chargé avec succès depuis: {self.model_path}")
                
                # Afficher les informations du modèle
                logger.info(f"📊 Shape d'entrée: {self.model.input_shape}")
                logger.info(f"📊 Shape de sortie: {self.model.output_shape}")
            else:
                logger.error(f"❌ Modèle non trouvé: {self.model_path}")
                self.model = None
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement du modèle: {str(e)}")
            self.model = None
    
    def preprocess_image(self, image_path):
        """
        Préprocesse l'image pour la prédiction
        
        Args:
            image_path (str): Chemin vers l'image
            
        Returns:
            np.array: Image préprocessée
        """
        try:
            # Charger l'image avec la taille attendue par le modèle (224x224)
            img = image.load_img(image_path, target_size=(224, 224))
            
            # Convertir en array et normaliser
            img_array = image.img_to_array(img)
            img_array = img_array / 255.0  # Normalisation [0,1]
            
            # Ajouter la dimension batch
            img_array = np.expand_dims(img_array, axis=0)
            
            logger.info(f"📷 Image préprocessée: {img_array.shape}")
            return img_array
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du préprocessing: {str(e)}")
            return None
    
    def predict(self, image_path):
        """
        Fait une prédiction sur l'image
        
        Args:
            image_path (str): Chemin vers l'image
            
        Returns:
            dict: Résultat de la prédiction avec label et confiance
        """
        if self.model is None:
            logger.error("❌ Modèle non chargé")
            return {
                'error': 'Modèle non disponible',
                'label': 'Error',
                'confidence': 0.0
            }
        
        try:
            # Préprocesser l'image
            processed_image = self.preprocess_image(image_path)
            if processed_image is None:
                return {
                    'error': 'Erreur de préprocessing',
                    'label': 'Error',
                    'confidence': 0.0
                }
            
            # Faire la prédiction
            prediction = self.model.predict(processed_image, verbose=0)[0][0]
            
            # Interpréter le résultat selon votre spécification
            # "Good" si pred > 0.5 else "anomaly"
            if prediction > 0.5:
                label = "Good"
                confidence = prediction  # La confiance pour Good
            else:
                label = "anomaly"
                confidence = 1 - prediction  # La confiance pour anomaly
            
            result = {
                'label': label,
                'confidence': float(confidence),
                'raw_prediction': float(prediction)
            }
            
            logger.info(f"🔍 Prédiction: {label} (confiance: {confidence*100:.2f}%)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la prédiction: {str(e)}")
            return {
                'error': str(e),
                'label': 'Error',
                'confidence': 0.0
            }
    
    def is_model_available(self):
        """
        Vérifie si le modèle est disponible
        """
        return self.model is not None


# Instance globale du prédicteur
predictor = ImagePredictor()
