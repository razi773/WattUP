# Fichier README pour le modèle ML

## Instructions pour le modèle best_model.keras

Pour que la fonctionnalité de prédiction d'images fonctionne, vous devez :

1. Placer votre modèle entraîné `best_model.keras` dans ce répertoire
2. Le modèle doit accepter des images de taille 224x224 pixels
3. Le modèle doit retourner une prédiction binaire (0 ou 1)
   - 0 = Normal/Good
   - 1 = Anomaly

## Structure attendue du modèle :
```
ml_models/
└── best_model.keras  (votre modèle entraîné)
```

## Formats d'images supportés :
- JPEG/JPG
- PNG  
- GIF
- Taille max : 10MB

## Configuration actuelle :
- Preprocessing : Redimensionnement à 224x224, normalisation [0,1]
- Classification : Binaire avec seuil à 0.5
- Labels : 'Good' si prédiction < 0.5, 'Anomaly' si >= 0.5
