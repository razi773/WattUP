# -*- coding: utf-8 -*-
"""
Module documentation
"""

import numpy as np
import pandas as pd
from pymongo import MongoClient
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Input
client = MongoClient("mongodb://localhost:27017/")
db = client["energy_db"]
daily_collection = db["daily_data"]
predict_collection = db["predicted_data"]
def train_and_predict_lstm():
    print("📥 [LSTM] Chargement des données depuis MongoDB...")
    cursor = daily_collection.find({}, {"_id": 0, "date": 1, "total_active_pow": 1})
    df = pd.DataFrame(cursor)
    if df.empty:
        print("❌ [LSTM] Aucune donnée trouvée dans la collection daily_data.")
        return None
    print("📊 [LSTM] Préparation des données...")
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date', 'total_active_pow'])
    df = df.sort_values('date')
    values = df['total_active_pow'].astype(float).values.reshape(-1, 1)
    scaler = MinMaxScaler()
    scaled_values = scaler.fit_transform(values)
    window = 14
    X, y = [], []
    for i in range(len(scaled_values) - window):
        X.append(scaled_values[i:i + window])
        y.append(scaled_values[i + window])
    X, y = np.array(X), np.array(y)
    if len(X) < 30:
        print("⚠️ [LSTM] Pas assez de données pour entraîner un modèle. Taille :", len(X))
        return None
    split = int(0.8 * len(X))
    X_train, y_train = X[:split], y[:split]
    print(f"🧠 [LSTM] Entraînement du modèle ({len(X_train)} séquences)...")
    model = Sequential([
        Input(shape=(window, 1)),
        LSTM(64, activation='tanh'),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    model.fit(X_train, y_train, epochs=1, batch_size=8, verbose=1)
    print("🔮 [LSTM] Prédiction des 30 jours suivants...")
    future_preds = []
    last_seq = scaled_values[-window:]
    current_seq = last_seq.copy()
    for _ in range(30):
        pred = model.predict(current_seq.reshape(1, window, 1), verbose=0)[0, 0]
        future_preds.append(pred)
        current_seq = np.append(current_seq[1:], [[pred]], axis=0)
    future_values = scaler.inverse_transform(np.array(future_preds).reshape(-1, 1)).flatten()
    future_dates = pd.date_range(start=df['date'].max() + pd.Timedelta(days=1), periods=len(future_values))
    print("✅ Longueur dates :", len(future_dates))
    print("✅ Longueur valeurs :", len(future_values))
    print("✅ Exemple date:", future_dates[0])
    print("✅ Exemple valeur:", future_values[0])
    if len(future_dates) != len(future_values):
        raise ValueError("Mismatch entre future_dates et future_values")
    result_df = pd.DataFrame({
        "date": future_dates,
        "total_active_pow": future_values,
        "source": "LSTM"
    })
    print("🧹 [LSTM] Nettoyage et sauvegarde dans MongoDB (predicted_data)...")
    predict_collection.delete_many({})
    predict_collection.insert_many(result_df.to_dict(orient="records"))
    print("✅ [LSTM] Prédiction terminée et sauvegardée.")
    return result_df
