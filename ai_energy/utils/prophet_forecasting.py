# -*- coding: utf-8 -*-
"""
Module documentation
"""

from prophet import Prophet
import pandas as pd
def prepare_data_for_prophet(df, value_column='smoothed'):
    prophet_df = df[['date', value_column]].rename(columns={'date': 'ds', value_column: 'y'})
    prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])
    return prophet_df
def train_forecast_prophet(df, periods=30):
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode='multiplicative',
        changepoint_prior_scale=0.05
    )
    model.fit(df)
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
