# -*- coding: utf-8 -*-
"""
Module documentation
"""

from django.contrib import admin
from django.urls import path, include
from ai_energy import views as energy_views
from face_auth import views as face_views
from ai_energy.views import detect_anomalies_view
urlpatterns = [
    path('admin/', admin.site.urls),
    path('analyse-csv/', energy_views.analyse_csv, name='analyse_csv'),
    path('voir-lstm/', energy_views.voir_lstm, name='voir_lstm'),
    path('voir-xgb/', energy_views.voir_xgb, name='voir_xgb'),
    path('anomalies/', detect_anomalies_view, name='anomalies'),
    path('auth/', include('face_auth.urls')),
    path('', face_views.login_view, name='home'),
]
