# -*- coding: utf-8 -*-
"""
Django settings - sans .env (variables codées en dur)
"""

import os
from pathlib import Path
from pymongo import MongoClient

# 📁 Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# 🔐 Django settings
SECRET_KEY = 'django-insecure-your-temp-key'
DEBUG = True
ALLOWED_HOSTS = ["*"]

# 🧩 Apps installées
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ai_energy',
    'face_auth',
    'django_crontab',
]

# 🔐 Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'AI_Energy_Analyzer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'AI_Energy_Analyzer.wsgi.application'

# 📦 Base de données
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 🔑 Validation mot de passe
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
]

# 🌍 Internationalisation
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# 📂 Fichiers statiques
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 📧 Email SMTP (via Gmail) — remplacé par valeurs directes
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'azizturki111@gmail.com'
EMAIL_HOST_PASSWORD = 'ttua suhx riiq oaai'  # mot de passe d'application Gmail
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_DEBUG = True

# 🛢️ MongoDB — remplacé par valeurs directes
MONGO_USER = "admin"
MONGO_PASS = "adminpass"
MONGO_HOST = "mongodb"
MONGO_PORT = 27017
MONGO_DB_NAME = "energy_db"
MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}"

# ✅ Connexion Mongo
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
daily_collection = db["daily_data"]
prediction_collection = db["lstm_predictions"]

# 🕑 Cron Jobs
CRONJOBS = [
    ('0 0 1 * *', 'django.core.management.call_command', ['predict_xgb']),
]

# ✅ Debug print
print("EMAIL_HOST_USER =", EMAIL_HOST_USER)
print("MONGO_URI =", MONGO_URI)
