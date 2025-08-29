# -*- coding: utf-8 -*-
"""
Module documentation
"""

import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Model
from keras.layers import Input, Dense
from keras.callbacks import EarlyStopping
def train_autoencoder_model(df, feature_cols, encoding_dim=8, epochs=100, batch_size=16):
    """
    Entraîne un autoencoder sur les colonnes spécifiées du DataFrame df.
    :param df: DataFrame avec les données.
    :param feature_cols: Liste des colonnes utilisées pour l'entraînement.
    :return: autoencoder entraîné + scaler
    """
    X = df[feature_cols].copy()
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    input_dim = X_scaled.shape[1]
    input_layer = Input(shape=(input_dim,))
    encoder = Dense(32, activation='relu')(input_layer)
    encoder = Dense(encoding_dim, activation='relu')(encoder)
    decoder = Dense(32, activation='relu')(encoder)
    output_layer = Dense(input_dim, activation='linear')(decoder)
    autoencoder = Model(inputs=input_layer, outputs=output_layer)
    autoencoder.compile(optimizer='adam', loss='mse')
    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    autoencoder.fit(X_scaled, X_scaled,
                    epochs=epochs,
                    batch_size=batch_size,
                    shuffle=True,
                    validation_split=0.1,
                    callbacks=[early_stop],
                    verbose=0)
    print("✅ Autoencoder entraîné avec succès.")
    return autoencoder, scaler
def detect_anomalies(autoencoder, scaler, df, feature_cols, threshold=None):
    """
    Détecte les anomalies via l'autoencoder entraîné.
    :param autoencoder: modèle Keras entraîné
    :param scaler: scaler MinMaxScaler utilisé pendant l'entraînement
    :param df: DataFrame original
    :param feature_cols: colonnes utilisées pour la détection
    :param threshold: seuil de détection (None = calculé automatiquement via le 95e percentile)
    :return: DataFrame avec colonnes ['date', 'reconstruction_error', 'is_anomaly']
    """
    X = df[feature_cols].copy()
    X_scaled = scaler.transform(X)
    reconstructed = autoencoder.predict(X_scaled, verbose=0)
    mse = np.mean(np.power(X_scaled - reconstructed, 2), axis=1)
    if threshold is None:
        threshold = np.percentile(mse, 95)
        print(f"📊 Seuil automatique fixé à : {threshold:.6f}")
    df_result = df.copy()
    df_result['reconstruction_error'] = mse
    df_result['is_anomaly'] = df_result['reconstruction_error'] > threshold
    print(f"⚠️ Nombre d'anomalies détectées : {df_result['is_anomaly'].sum()} / {len(df_result)}")
    return df_result[['date', 'reconstruction_error', 'is_anomaly']]
