import os
import json
import numpy as np
import pandas as pd
from django.shortcuts import render
from django.http import JsonResponse
from pymongo import MongoClient

from .forms import UploadCSVForm
from ai_energy.utils.analyse_csv import analyser_csv
from ai_energy.utils.zephyr_api import envoyer_a_zephyr
from ai_energy.utils.rag_query import interroger_rag
from ai_energy.utils.generate_prompt import generer_prompt
from ai_energy.utils.lstm_predict import train_and_predict_lstm
from ai_energy.utils.predict_xgboost import predict_next_30_days_xgb
from .utils.autoencoder_anomaly import train_autoencoder_model, detect_anomalies
from ai_energy.utils.generer_rapport_anomalie import generer_rapport_anomalie


# 📦 Connexion MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["energy_db"]
predict_collection = db["predicted_data"]
xgb_collection = db["xgb_predictions"]

def voir_lstm(request):
    predictions = list(predict_collection.find({}, {"_id": 0, "date": 1, "total_active_pow": 1}))
    if not predictions:
        return render(request, 'voir_lstm.html', {"erreur": "Aucune prédiction disponible."})

    for p in predictions:
        p['date'] = pd.to_datetime(p['date']).strftime('%Y-%m-%d')
        p['prediction'] = round(p['total_active_pow'], 2)

    return render(request, 'voir_lstm.html', {"data": predictions})

def voir_xgb(request):
    predictions = list(xgb_collection.find({}, {"_id": 0, "date": 1, "total_active_pow": 1}))
    if not predictions:
        return render(request, 'voir_xgb.html', {"erreur": "Aucune prédiction XGBoost disponible."})

    for p in predictions:
        p['date'] = pd.to_datetime(p['date']).strftime('%Y-%m-%d')
        p['prediction'] = round(p['total_active_pow'], 2)

    return render(request, 'voir_xgb.html', {"data": predictions})

def extract_target_column(df, date_col='date', target_col='total_active_pow'):
    try:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        result = df[[date_col, target_col]].copy()
        result.columns = ['date', 'total_active_pow']
        return result
    except Exception as e:
        raise ValueError(f"Erreur d'extraction: {str(e)}")

def auto_extract_consumption_column(df):
    df.columns = [c.lower() for c in df.columns]
    if 'date' in df.columns and 'time' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], dayfirst=True, errors='coerce')
        df = df.rename(columns={'datetime': 'date'})
    elif 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    else:
        raise ValueError("Aucune colonne date valide détectée.")

    candidates = ['total_active_pow', 'global_active_power', 'power', 'consommation']
    for col in df.columns:
        if col.lower().strip() in candidates:
            df = df.rename(columns={col: 'total_active_pow'})
            break
    if 'total_active_pow' not in df.columns:
        raise ValueError("Aucune colonne de consommation identifiable ('total_active_pow') détectée.")

    df = df.dropna(subset=['date', 'total_active_pow'])
    df['total_active_pow'] = pd.to_numeric(df['total_active_pow'], errors='coerce')
    df = df.dropna(subset=['total_active_pow'])

    return df

client = MongoClient("mongodb://localhost:27017/")
db = client["energy_db"]
predict_collection = db["predicted_data"]
xgb_collection = db["xgb_predictions"]

def analyse_csv(request):
    résumé = rag_context = réponse = lstm_result = None
    xgb_result = None
    rapport_anomalie = None  # Ajout ici

    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            temp_path = f"/tmp/{csv_file.name}"
            with open(temp_path, 'wb+') as destination:
                for chunk in csv_file.chunks():
                    destination.write(chunk)

            résumé, df = analyser_csv(temp_path)
            rag_context = interroger_rag(résumé)
            prompt = generer_prompt(résumé, rag_context)

            try:
                réponse = envoyer_a_zephyr(prompt)
            except Exception as e:
                réponse = f"Erreur Zephyr : {str(e)}"

            action = request.POST.get('action')

            if action == 'predict_lstm':
                try:
                    lstm_result = train_and_predict_lstm()
                except Exception as e:
                    print("Erreur LSTM:", e)

            elif action == 'predict_xgb':
                try:
                    predict_next_30_days_xgb(df)
                    xgb_result = True

                    # Générer anomalies + rapport
                    df_analyse = pd.read_csv("data/daily_total_by_day.csv")
                    df_analyse['date'] = pd.to_datetime(df_analyse['date'])
                    if 'smoothed' not in df_analyse.columns:
                        df_analyse['smoothed'] = df_analyse['total_active_pow'].rolling(window=3, center=True).mean()
                        df_analyse['smoothed'] = df_analyse['smoothed'].bfill().ffill()
                    df_analyse = df_analyse.bfill().ffill()

                    df_analyse['day_of_week'] = df_analyse['date'].dt.dayofweek
                    df_analyse['month'] = df_analyse['date'].dt.month
                    df_analyse['dayofyear_sin'] = np.sin(2 * np.pi * df_analyse['date'].dt.dayofyear / 365)
                    df_analyse['dayofyear_cos'] = np.cos(2 * np.pi * df_analyse['date'].dt.dayofyear / 365)

                    model, scaler = train_autoencoder_model(df_analyse, ['smoothed', 'day_of_week', 'month', 'dayofyear_sin', 'dayofyear_cos'])
                    anomalies_df = detect_anomalies(model, scaler, df_analyse, ['smoothed', 'day_of_week', 'month', 'dayofyear_sin', 'dayofyear_cos'])
                    rapport_anomalie = generer_rapport_anomalie(anomalies_df)

                except Exception as e:
                    print("Erreur XGBoost:", e)
                    xgb_result = False
    else:
        form = UploadCSVForm()

    # Forecast Prophet (généré toujours)
    anomalies = None
    try:
        df_analyse = pd.read_csv("data/daily_total_by_day.csv")
        df_analyse['date'] = pd.to_datetime(df_analyse['date'])
        if 'smoothed' not in df_analyse.columns:
            df_analyse['smoothed'] = df_analyse['total_active_pow'].rolling(window=3, center=True).mean()
            df_analyse['smoothed'] = df_analyse['smoothed'].bfill().ffill()
        df_analyse = df_analyse.bfill().ffill()
        df_analyse['day_of_week'] = df_analyse['date'].dt.dayofweek
        df_analyse['month'] = df_analyse['date'].dt.month
        df_analyse['dayofyear_sin'] = np.sin(2 * np.pi * df_analyse['date'].dt.dayofyear / 365)
        df_analyse['dayofyear_cos'] = np.cos(2 * np.pi * df_analyse['date'].dt.dayofyear / 365)
        model, scaler = train_autoencoder_model(df_analyse, ['smoothed', 'day_of_week', 'month', 'dayofyear_sin', 'dayofyear_cos'])
        anomalies_df = detect_anomalies(model, scaler, df_analyse, ['smoothed', 'day_of_week', 'month', 'dayofyear_sin', 'dayofyear_cos'])
        anomalies = anomalies_df.to_dict(orient="records")
    except Exception as e:
        print("Erreur anomalies/forecast:", e)

    return render(request, 'upload.html', {
        'form': form,
        'résumé': résumé,
        'rag_context': rag_context,
        'réponse_gpt': réponse,
        'lstm_result': lstm_result is not None,
        'xgb_result': xgb_result,
        'anomalies': anomalies,
        'rapport_anomalie': rapport_anomalie,
        'resultats': request.method == 'POST' and request.POST.get('action') in ['predict_lstm', 'predict_xgb'],
    })
# API JSON : Anomalies
def detect_anomalies_view(request):
    df = pd.read_csv("data/daily_total_by_day.csv")
    df['date'] = pd.to_datetime(df['date'])
    df.fillna(method='bfill', inplace=True)

    df['day_of_week'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    df['dayofyear_sin'] = np.sin(2 * np.pi * df['date'].dt.dayofyear / 365)
    df['dayofyear_cos'] = np.cos(2 * np.pi * df['date'].dt.dayofyear / 365)

    features = ['smoothed', 'day_of_week', 'month', 'dayofyear_sin', 'dayofyear_cos']
    model, scaler = train_autoencoder_model(df, features)
    results = detect_anomalies(model, scaler, df, features)
    return JsonResponse(results.to_dict(orient="records"), safe=False)

