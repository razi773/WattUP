# -*- coding: utf-8 -*-
"""
Module documentation
"""

import pandas as pd
import os
from sklearn.ensemble import IsolationForest
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from pymongo import MongoClient
from ai_energy.lstm_views import auto_extract_consumption_column
client = MongoClient("mongodb://localhost:27017/")
db = client["energy_db"]
daily_collection = db["daily_data"]
def analyser_csv(csv_path):
    _, ext = os.path.splitext(csv_path)
    if ext.lower() == ".txt":
        df_raw = pd.read_csv(csv_path, sep=';', engine='python')
    else:
        df_raw = pd.read_csv(csv_path)
    df = auto_extract_consumption_column(df_raw)
    df['total_active_pow'] = pd.to_numeric(df['total_active_pow'], errors='coerce')
    df = df.dropna(subset=['total_active_pow'])
    df['dayofweek'] = df['date'].dt.dayofweek
    df['is_weekend'] = df['dayofweek'] >= 5
    df['rolling_mean_7'] = df['total_active_pow'].rolling(7).mean()
    df['lag_1'] = df['total_active_pow'].shift(1)
    df['diff_1'] = df['total_active_pow'].diff()
    df = df.dropna()
    model_iso = IsolationForest(contamination=0.05, random_state=42)
    df['anomaly'] = model_iso.fit_predict(df[['total_active_pow']])
    df['is_anomaly'] = df['anomaly'] == -1
    features = ['dayofweek', 'is_weekend', 'rolling_mean_7', 'lag_1', 'diff_1']
    X = df[features]
    y = df['total_active_pow']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    model = XGBRegressor()
    model.fit(X_train, y_train)
    df['prediction'] = model.predict(X)
    conso_moy = df['total_active_pow'].mean()
    conso_totale = df['total_active_pow'].sum()
    pic = df['total_active_pow'].max()
    date_pic = df[df['total_active_pow'] == pic]['date'].values[0]
    nb_anomalies = df['is_anomaly'].sum()
    dates_anomalies = df[df['is_anomaly']]['date'].dt.strftime('%Y-%m-%d').tolist()
    prediction_mois = df['prediction'][-30:].sum()
    resume = f"""📊 Résumé énergétique :
- Moyenne : {conso_moy:.2f} kWh
- Totale : {conso_totale:.2f} kWh
- Pic : {pic:.2f} kWh le {pd.to_datetime(date_pic).strftime('%Y-%m-%d')}
⚠️ Anomalies : {nb_anomalies} | {', '.join(dates_anomalies[:5])}
🔮 Prédiction mois suivant : {prediction_mois:.2f} kWh"""
    daily_collection.delete_many({})
    daily_collection.insert_many(df.to_dict(orient="records"))
    return resume.strip(), df