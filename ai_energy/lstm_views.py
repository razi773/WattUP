# -*- coding: utf-8 -*-
"""
Module documentation
"""

from django.shortcuts import render
from pymongo import MongoClient
import pandas as pd
from ai_energy.utils.lstm_predict import train_and_predict_lstm
client = MongoClient("mongodb://localhost:27017/")
db = client["energy_db"]
predict_collection = db["predicted_data"]
def voir_lstm(request):
    predictions = list(predict_collection.find({}, {"_id": 0, "date": 1, "total_active_pow": 1}))
    if not predictions:
        return render(request, 'voir_lstm.html', {"erreur": "Aucune prédiction disponible."})
    for p in predictions:
        p['date'] = pd.to_datetime(p['date']).strftime('%Y-%m-%d')
        p['prediction'] = round(p['total_active_pow'], 2)
    return render(request, 'voir_lstm.html', {"data": predictions})
def extract_target_column(df, date_col='date', target_col='total_active_pow'):
    try:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        result = df[[date_col, target_col]].copy()
        result.columns = ['date', 'total_active_pow']
        return result
    except Exception as e:
        raise ValueError(f"Erreur d'extraction: {str(e)}")
import re
def auto_extract_consumption_column(df):
    date_col = None
    for col in df.columns:
        if 'date' in col.lower():
            date_col = col
            break
    if not date_col:
        df['date'] = pd.date_range(start='2023-01-01', periods=len(df), freq='D')
        date_col = 'date'
    target_col = None
    patterns = ['consommation', 'power', 'energy', 'conso', 'kwh', 'kw','total_active_pow', 'global_active_power']
    for col in df.columns:
        for pattern in patterns:
            if re.search(pattern, col.lower()):
                target_col = col
                break
        if target_col:
            break
    if not target_col:
        raise ValueError("Aucune colonne de consommation énergétique détectée automatiquement.")
    df = df[[date_col, target_col]].copy()
    df.columns = ['date', 'total_active_pow']
    df['date'] = pd.to_datetime(df['date'])
    return df
