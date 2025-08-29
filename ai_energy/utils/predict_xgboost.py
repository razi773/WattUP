# -*- coding: utf-8 -*-
"""
Module documentation
"""

import numpy as np
import pandas as pd
from pymongo import MongoClient
from xgboost import XGBRegressor
from sklearn.ensemble import IsolationForest
client = MongoClient("mongodb://localhost:27017/")
db = client["energy_db"]
xgb_collection = db["xgb_predictions"]
daily_collection = db["daily_data"]
def predict_next_30_days_xgb(df):
    print("⚙️ [XGBoost] Nettoyage des données et préparation...")
    iso = IsolationForest(contamination=0.02, random_state=42)
    df = df.copy()
    df['anomaly'] = iso.fit_predict(df[['total_active_pow']])
    df = df[df['anomaly'] == 1]
    df.drop(columns='anomaly', inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    df['dayofweek'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    df['is_weekend'] = df['dayofweek'] >= 5
    df['rolling_mean_7'] = df['total_active_pow'].rolling(7).mean()
    df['rolling_mean_30'] = df['total_active_pow'].rolling(30).mean()
    df['lag_1'] = df['total_active_pow'].shift(1)
    df['diff_1'] = df['total_active_pow'].diff()
    df = df.dropna()
    features = ['dayofweek', 'month', 'is_weekend', 'rolling_mean_7', 'rolling_mean_30', 'lag_1', 'diff_1']
    X = df[features]
    y = df['total_active_pow']
    model = XGBRegressor(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42
    )
    model.fit(X, y)
    print("📈 [XGBoost] Prédiction des 30 prochains jours...")
    last_row = df.iloc[-1].copy()
    preds = []
    dates = []
    for i in range(30):
        features_input = pd.DataFrame([last_row[features]])
        pred = model.predict(features_input)[0]
        preds.append(pred)
        next_date = last_row['date'] + pd.Timedelta(days=1)
        dates.append(next_date)
        last_row['date'] = next_date
        last_row['dayofweek'] = next_date.dayofweek
        last_row['month'] = next_date.month
        last_row['is_weekend'] = next_date.dayofweek >= 5
        last_row['rolling_mean_7'] = df['total_active_pow'].iloc[-7:].mean()
        last_row['rolling_mean_30'] = df['total_active_pow'].iloc[-30:].mean() if len(df) >= 30 else df['total_active_pow'].mean()
        last_row['lag_1'] = pred
        last_row['diff_1'] = pred - last_row['lag_1']
        df = pd.concat([df, pd.DataFrame([{'date': next_date, 'total_active_pow': pred}])], ignore_index=True)
    result_df = pd.DataFrame({
        "date": dates,
        "total_active_pow": preds,
        "source": "XGBoost"
    })
    print("🧹 [XGBoost] Remplacement des anciennes prédictions XGBoost...")
    predicted_collection = db["predicted_data"]
    cost_collection = db["cost_predictions"]
    old_xgb_count = xgb_collection.count_documents({"source": "XGBoost"})
    old_predicted_count = predicted_collection.count_documents({"source": "XGBoost"})
    old_cost_count = cost_collection.count_documents({"source": "XGBoost"})
    print(f"🗑️  [XGBoost] Suppression de {old_xgb_count} anciennes prédictions XGBoost...")
    print(f"🗑️  [XGBoost] Suppression de {old_predicted_count} anciennes données prédites...")
    print(f"🗑️  [XGBoost] Suppression de {old_cost_count} anciennes prédictions de coût...")
    xgb_collection.delete_many({"source": "XGBoost"})
    predicted_collection.delete_many({"source": "XGBoost"})
    cost_collection.delete_many({"source": "XGBoost"})
    print("💾 [XGBoost] Sauvegarde des nouvelles prédictions...")
    xgb_collection.insert_many(result_df.to_dict(orient="records"))
    predicted_collection.insert_many(result_df.to_dict(orient="records"))
    print("💰 [XGBoost] Génération des prédictions de coût...")
    cost_predictions = []
    for _, row in result_df.iterrows():
        daily_cost = row['total_active_pow'] * 0.15
        cost_predictions.append({
            'date': row['date'].strftime('%Y-%m-%d'),
            'predicted_cost': daily_cost,
            'predicted_consumption': row['total_active_pow'],
            'source': 'XGBoost'
        })
    cost_collection.insert_many(cost_predictions)
    print(f"✅ [XGBoost] Remplacement terminé! {len(result_df)} nouvelles prédictions et {len(cost_predictions)} coûts sauvegardés.")
