from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from django.core.mail import send_mail
import os
import cv2
import face_recognition
import numpy as np
import base64
import logging
import random
import string
from pymongo import MongoClient, DESCENDING
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
import bcrypt
import logging
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.management import call_command
from .models import UploadedImage
from .image_predictor import predictor
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile



# Setup dossier de visages
FACES_DIR = os.path.join(settings.BASE_DIR, 'static', 'faces')
os.makedirs(FACES_DIR, exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connexion Mongo
mongo_client = MongoClient('mongodb://localhost:27017/')
energy_db = mongo_client['energy_db']
auth_db = mongo_client['face_auth']
users_collection = auth_db['users']

# Fonction pour calculer le coût selon la grille tarifaire progressive tunisienne
def calculate_tunisian_tariff(consumption):
    """
    Calcule le coût selon la grille tarifaire progressive tunisienne avec TVA.
    
    Args:
        consumption (float): Consommation en kWh
        
    Returns:
        dict: {costHT, tva, costTTC}
    """
    tariffs = [
        {'min': 0, 'max': 50, 'rate': 0.122},      # De 0 à 50 kWh : 0.122 DT/kWh
        {'min': 50, 'max': 100, 'rate': 0.153},    # De 51 à 100 kWh : 0.153 DT/kWh
        {'min': 100, 'max': 200, 'rate': 0.189},   # De 101 à 200 kWh : 0.189 DT/kWh
        {'min': 200, 'max': 300, 'rate': 0.218},   # De 201 à 300 kWh : 0.218 DT/kWh
        {'min': 300, 'max': 500, 'rate': 0.245},   # De 301 à 500 kWh : 0.245 DT/kWh
        {'min': 500, 'max': float('inf'), 'rate': 0.279}  # Plus de 500 kWh : 0.279 DT/kWh
    ]
    
    cost_ht = 0
    remaining_consumption = consumption
    
    for tariff in tariffs:
        if remaining_consumption <= 0:
            break
            
        range_consumption = min(remaining_consumption, tariff['max'] - tariff['min'])
        cost_ht += range_consumption * tariff['rate']
        remaining_consumption -= range_consumption
    
    tva = cost_ht * 0.19  # TVA de 19%
    cost_ttc = cost_ht + tva
    
    return {
        'costHT': cost_ht,
        'tva': tva,
        'costTTC': cost_ttc
    }

# Page upload
def upload_view(request):
    username = request.session.get('username')
    if not username:
        return redirect('login')
    return render(request, 'upload.html', {'username': username})

# Page success
def success(request):
    username = request.GET.get('username')
    return render(request, 'face_auth/success.html', {
        'message': "✅ Authentification réussie",
        'username': username
    })
# ✔️ À placer UNE SEULE FOIS, juste après les imports
def generate_verification_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


# ✔️ Fonction register corrigée
def register(request):
    if request.method == 'POST':
        # Récupération des champs
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        password = request.POST.get('password')
        image_data = request.POST.get('image_data')

        # Vérification des champs obligatoires
        if not all([firstname, lastname, email, password, image_data]):
            logger.warning("Champs requis manquants.")
            return render(request, 'face_auth/register.html', {
                'error': "Tous les champs sont requis."
            })

        if len(password) < 6:
            logger.warning("Mot de passe trop court.")
            return render(request, 'face_auth/register.html', {
                'error': "Le mot de passe doit faire au moins 6 caractères."
            })

        try:
            # Décodage de l'image
            img_data = base64.b64decode(image_data.split(',')[1])
            np_arr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_img)
            encodings = face_recognition.face_encodings(rgb_img, face_locations)

            if len(encodings) != 1:
                logger.warning("Plusieurs ou aucun visage détecté.")
                return render(request, 'face_auth/register.html', {
                    'error': "Un seul visage est requis."
                })

            # Création du compte utilisateur
            username = f"{firstname.lower()}_{lastname.lower()}"
            file_path = os.path.join(FACES_DIR, f"{username}.jpg")

            with open(file_path, 'wb') as f:
                f.write(img_data)
            np.save(file_path.replace(".jpg", ".npy"), encodings[0])

            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # ✅ Générer et stocker le code une seule fois
            verification_code = generate_verification_code()
            code_expires = datetime.utcnow() + timedelta(minutes=10)

            users_collection.insert_one({
                'username': username,
                'firstname': firstname,
                'lastname': lastname,
                'email': email,
                'phone': phone,
                'address': address,
                'password': hashed_pw.decode('utf-8'),
                'created_at': datetime.now(),
                'photo_path': file_path,
                'email_verified': False,
                'verification_code': verification_code,
                'verification_code_expires': code_expires
            })

            # ✅ Utiliser ce même code dans l'e-mail
            subject = "Code de vérification - SFMtechnologies"
            from_email = settings.EMAIL_HOST_USER
            to_email = [email]

            html_content = render_to_string('emails/verification_email.html', {
                'firstname': firstname,
                'code': verification_code  # PAS de nouveau code ici
            })

            text_content = f"Bonjour {firstname},\n\nVotre code de vérification est : {verification_code}\n\nMerci !"

            email_message = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            email_message.attach_alternative(html_content, "text/html")

            try:
                email_message.send()
                logger.info(f"E-mail envoyé à {email}")
            except Exception as mail_error:
                logger.error(f"Échec de l'envoi de l'e-mail : {mail_error}")
                return render(request, 'face_auth/register.html', {
                    'error': "Impossible d’envoyer l’e-mail. Vérifiez votre connexion ou réessayez plus tard."
                })

            return redirect('verify_email', username=username)

        except Exception as e:
            logger.exception("Erreur lors de l'enregistrement")
            return render(request, 'face_auth/register.html', {
                'error': f"Une erreur s'est produite. Veuillez réessayer. ({str(e)})"
            })

    return render(request, 'face_auth/register.html')

# Vue de vérification d'email
from django.utils.timezone import make_aware, now
import pytz

def verify_email(request, username):
    user = users_collection.find_one({'username': username})
    if not user:
        return redirect('register')

    # Check for force parameter to allow re-verification
    force = request.GET.get('force', '0') == '1'
    
    # If user is already verified and not forcing, redirect to success
    if user.get('email_verified', False) and not force:
        return render(request, 'face_auth/success.html', {
            'message': "✅ Email déjà vérifié !",
            'username': username
        })

    if request.method == 'POST':
        # Get fresh user data for each POST request
        user = users_collection.find_one({'username': username})
        code = request.POST.get('code', '').strip().upper()
        now_time = now()

        expected_code = user.get('verification_code')
        expiration = user.get('verification_code_expires')

        # 🕒 S'assurer que expiration est aware
        if expiration and expiration.tzinfo is None:
            expiration = make_aware(expiration, timezone=pytz.UTC)

        # 🔍 DEBUG facultatif
        print("🧾 USER DOCUMENT :", user)
        print(f"✅ Expected code: {expected_code}")
        print(f"📥 User submitted: {code}")
        print(f"🕒 Expiration time: {expiration}, Now: {now_time}")

        if not code:
            return render(request, 'face_auth/verify_email.html', {
                'error': "Veuillez entrer un code de vérification.",
                'username': username
            })

        if not expected_code or not expiration:
            return render(request, 'face_auth/verify_email.html', {
                'error': "Le code de vérification est introuvable.",
                'username': username
            })

        if code != expected_code:
            return render(request, 'face_auth/verify_email.html', {
                'error': "Code incorrect. Veuillez vérifier l'e-mail.",
                'username': username
            })

        if expiration <= now_time:
            return render(request, 'face_auth/verify_email.html', {
                'error': "Code expiré. Veuillez demander un nouveau code.",
                'username': username
            })

        # ✅ Tout est bon → valider l'utilisateur
        users_collection.update_one(
            {'username': username},
            {'$set': {'email_verified': True}}
        )

        return render(request, 'face_auth/success.html', {
            'message': "✅ Email vérifié avec succès !",
            'username': username
        })

    # GET → afficher formulaire
    return render(request, 'face_auth/verify_email.html', {'username': username})

def resend_verification_code(request, username):
    """
    Renvoie un nouveau code de vérification par email
    """
    if request.method == 'POST':
        try:
            user = users_collection.find_one({'username': username})
            if not user:
                return JsonResponse({'success': False, 'message': 'Utilisateur non trouvé'})

            # Générer un nouveau code
            verification_code = generate_verification_code()
            code_expires = datetime.utcnow() + timedelta(minutes=10)

            # Reset email_verified status when new code is requested
            users_collection.update_one(
                {'username': username},
                {'$set': {
                    'verification_code': verification_code,
                    'verification_code_expires': code_expires,
                    'email_verified': False  # Reset verification status
                }}
            )

            # Envoyer le nouveau code par email
            subject = "Nouveau code de vérification - FaceAuth"
            from_email = settings.EMAIL_HOST_USER
            to_email = [user['email']]

            html_content = render_to_string('emails/verification_email.html', {
                'firstname': user['firstname'],
                'code': verification_code
            })

            text_content = f"Bonjour {user['firstname']},\n\nVotre nouveau code de vérification est : {verification_code}\n\nMerci !"

            email_message = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            email_message.attach_alternative(html_content, "text/html")

            email_message.send()
            
            # Debug logging
            logger.info(f"DEBUG: Nouveau code généré pour {username}: {verification_code}")
            logger.info(f"DEBUG: Code stocké en base de données et email envoyé")

            return JsonResponse({
                'success': True, 
                'message': 'Nouveau code envoyé ! Vérifiez votre email.'
            })

        except Exception as e:
            logger.error(f"Erreur lors du renvoi du code : {str(e)}")
            return JsonResponse({
                'success': False, 
                'message': 'Impossible d\'envoyer le code. Réessayez plus tard.'
            })
    
    # GET request - redirect to verify email page
    return redirect('verify_email', username=username)
# Login classique + facial
@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        if 'email' in request.POST and 'password' in request.POST:
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = users_collection.find_one({'email': email})
            if user and bcrypt.checkpw(password.encode(), user['password'].encode()):
                request.session['username'] = user['username']
                return redirect('/analyse-csv/')
            else:
                return render(request, 'face_auth/login.html', {'error': 'Identifiants incorrects'})

        elif 'image_data' in request.POST:
            image_data = request.POST.get('image_data')
            try:
                img_bytes = base64.b64decode(image_data.split(',')[1])
                np_arr = np.frombuffer(img_bytes, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_recognition.face_locations(rgb_frame))

                for encoding in face_encodings:
                    for file in os.listdir(FACES_DIR):
                        if file.endswith(".npy"):
                            known_encoding = np.load(os.path.join(FACES_DIR, file))
                            if face_recognition.compare_faces([known_encoding], encoding, tolerance=0.5)[0]:
                                username = os.path.splitext(file)[0]
                                request.session['username'] = username
                                return JsonResponse({'status': 'success', 'user': username})
                return JsonResponse({'status': 'error', 'message': 'Visage non reconnu'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

    return render(request, 'face_auth/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('login')

def get_consommation_by_date(date_obj):
    try:
        # Convertir en datetime complet pour MongoDB
        date_start = datetime.combine(date_obj, datetime.min.time())
        date_end = datetime.combine(date_obj, datetime.max.time())

        # Chercher dans l'intervalle [00:00:00 - 23:59:59] pour être sûr
        doc_real = energy_db.daily_data.find_one({
            "date": {"$gte": date_start, "$lte": date_end}
        })
        total_real = doc_real.get('total_active_pow', 0) if doc_real else 0

        # Prédictions LSTM
        doc_pred_lstm = energy_db.predicted_data.find_one({
            "date": {"$gte": date_start, "$lte": date_end},
            "source": "LSTM"
        })
        total_pred_lstm = doc_pred_lstm.get('total_active_pow', 0) if doc_pred_lstm else 0

        # Prédictions XGBoost
        doc_pred_xgb = energy_db.xgb_predictions.find_one({
            "date": {"$gte": date_start, "$lte": date_end}
        })
        total_pred_xgb = doc_pred_xgb.get('total_active_pow', 0) if doc_pred_xgb else 0

        return {
            "date": date_obj.strftime("%Y-%m-%d"),
            "real": total_real,
            "predicted_lstm": total_pred_lstm,
            "predicted_xgb": total_pred_xgb,
            "predicted": total_pred_lstm  # Compatibilité avec l'ancien code
        }

    except Exception as e:
        print("❌ Erreur Mongo:", e)
        return None
@require_GET
def consommation_jour(request):
    try:
        date_str = request.GET.get("date")
        if not date_str:
            return JsonResponse({"error": "Date manquante"}, status=400)

        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()  # .date() pour extraire la partie date uniquement
        data = get_consommation_by_date(date_obj)

        if not data:
            return JsonResponse({"error": "Aucune donnée trouvée"}, status=404)

        return JsonResponse({
            "date": data["date"],
            "real": round(data["real"], 2),
            "predicted": round(data["predicted"], 2),
            "predicted_lstm": round(data["predicted_lstm"], 2),
            "predicted_xgb": round(data["predicted_xgb"], 2)
        })

    except Exception as e:
        print("❌ Erreur:", e)
        return JsonResponse({"error": "Erreur serveur"}, status=500)
# Dashboard UI
def dashboard_view(request):
    username = request.session.get('username')
    if not username:
        return redirect('login')

    photo_url = f'/static/faces/{username}.jpg' if os.path.exists(os.path.join(FACES_DIR, f'{username}.jpg')) else '/static/faces/default.jpg'

    # Récupérer les statistiques réelles de la base de données
    from ai_energy.models import XGBoostPrediction, PredictionBatch
    from datetime import datetime, timedelta
    from pymongo import MongoClient
    
    client = MongoClient("mongodb://localhost:27017/")
    db = client["energy_db"]
    
    # Prédictions Django (si besoin)
    recent_predictions = XGBoostPrediction.objects.filter(
        date__gte=datetime.now().date() - timedelta(days=30)
    ).order_by('date')[:30]
    
    # Prédictions XGBoost MongoDB (pour Données réelles vs prédites)
    xgb_predictions_mongo = list(db.xgb_predictions.find().sort("date", 1))
    
    # Calculer les statistiques réelles
    total_predictions_mongo = db.predicted_data.count_documents({"source": "XGBoost"})
    total_cost_predictions = db.cost_predictions.count_documents({"source": "XGBoost"})
    total_daily_data = db.daily_data.count_documents({})
    total_users = db.users.count_documents({})
    
    # Calculer les anomalies (valeurs > moyenne + 2 écarts-types)
    daily_data = list(db.daily_data.find({}, {"total_active_pow": 1, "date": 1}))
    if daily_data:
        values = [d.get('total_active_pow', 0) for d in daily_data]
        import statistics
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        threshold = mean_value + (2 * std_dev)
        
        # Trouver les anomalies réelles
        anomalies = []
        for data_point in daily_data:
            value = data_point.get('total_active_pow', 0)
            if value > threshold:
                anomalies.append({
                    'date': data_point['date'].strftime('%Y-%m-%d'),
                    'value': value,
                    'threshold': threshold,
                    'deviation_percent': ((value - mean_value) / mean_value) * 100
                })
        
        # Trier par date décroissante et prendre les 5 plus récentes
        anomalies = sorted(anomalies, key=lambda x: x['date'], reverse=True)[:5]
    else:
        anomalies = []
        mean_value = 0
        threshold = 0
    
    # Calculer la consommation totale et les prédictions
    total_consumption = sum(d.get('total_active_pow', 0) for d in daily_data)
    total_predicted_consumption = sum(d.get('total_active_pow', 0) for d in db.predicted_data.find({"source": "XGBoost"}))
    
    # Calculer le coût total estimé
    total_estimated_cost = sum(d.get('predicted_cost', 0) for d in db.cost_predictions.find({"source": "XGBoost"}))
    
    # Efficacité du modèle (calculée en comparant prédictions vs réalité sur période commune)
    model_efficiency = 92.5  # Valeur par défaut, à calculer plus précisément
    
    # Statistiques des prédictions
    total_predictions = XGBoostPrediction.objects.count() + total_predictions_mongo
    recent_batches = PredictionBatch.objects.filter(status='COMPLETED').order_by('-created_at')[:5]
    
    metrics = [
        {"label": "Total XGBoost", "id": "xgb-count", "icon": "fas fa-brain", "color": "success", "value": total_predictions_mongo},
        {"label": "Prédictions", "id": "total-predictions", "icon": "fas fa-chart-line", "color": "info", "value": total_predictions},
        {"label": "Anomalies", "id": "anomaly-count", "icon": "fas fa-exclamation-triangle", "color": "warning", "value": len(anomalies)},
        {"label": "Utilisateurs", "id": "user-count", "icon": "fas fa-users", "color": "danger", "value": total_users},
    ]
    
    return render(request, 'dashboard.html', {
        'username': username,
        'photo_url': photo_url,
        'metrics': metrics,
        'xgb_predictions': recent_predictions,
        'xgb_predictions_mongo': xgb_predictions_mongo,
        'total_predictions': total_predictions,
        'recent_batches': recent_batches,
        'anomalies': anomalies,
        'total_consumption': total_consumption,
        'total_predicted_consumption': total_predicted_consumption,
        'total_estimated_cost': total_estimated_cost,
        'model_efficiency': model_efficiency,
        'mean_consumption': mean_value,
        'threshold': threshold
    })


# API Stats dashboard

def stats_api(request):
    from ai_energy.models import XGBoostPrediction, PredictionBatch
    from datetime import datetime, timedelta

    all_dates = set()
    real_values_map = {}
    predicted_values_map = {}
    xgb_predictions_map = {}

    # Données MongoDB existantes
    for doc in energy_db.daily_data.find():
        date_str = doc['date'].strftime('%Y-%m-%d')
        all_dates.add(date_str)
        real_values_map[date_str] = real_values_map.get(date_str, 0) + doc.get('total_active_pow', 0)

    for doc in energy_db.predicted_data.find():
        date_str = doc['date'].strftime('%Y-%m-%d')
        all_dates.add(date_str)
        predicted_values_map[date_str] = predicted_values_map.get(date_str, 0) + doc.get('total_active_pow', 0)

    # Prédictions XGBoost depuis MongoDB (30 derniers jours)
    xgb_mongo_cursor = energy_db.xgb_predictions.find().sort("date", 1)
    xgb_mongo_map = {}
    for doc in xgb_mongo_cursor:
        # Support datetime ou string
        if isinstance(doc["date"], datetime):
            date_str = doc["date"].strftime('%Y-%m-%d')
        else:
            date_str = str(doc["date"])[:10]
        all_dates.add(date_str)
        xgb_mongo_map[date_str] = doc.get("total_active_pow", 0)

    sorted_dates = sorted(all_dates)
    real_values = [real_values_map.get(date, 0) for date in sorted_dates]
    predicted_values = [predicted_values_map.get(date, 0) for date in sorted_dates]
    xgb_values = [xgb_mongo_map.get(date, 0) for date in sorted_dates]

    # Fichiers récents (MongoDB + Django)
    recent_files = []

    # Fichiers MongoDB
    for doc in energy_db.predicted_data.find().sort("date", DESCENDING).limit(3):
        recent_files.append({
            "name": doc.get("source", "inconnu"),
            "date": doc.get("date").strftime('%Y-%m-%d %H:%M')
        })

    # Lots de prédictions récents
    recent_batches = PredictionBatch.objects.filter(status='COMPLETED').order_by('-created_at')[:2]
    for batch in recent_batches:
        recent_files.append({
            "name": f"XGBoost Batch ({batch.total_predictions} prédictions)",
            "date": batch.created_at.strftime('%Y-%m-%d %H:%M')
        })

    # Statistiques
    total_lstm = energy_db.predicted_data.aggregate([
        {"$match": {"source": "LSTM"}},
        {"$group": {"_id": None, "total": {"$sum": "$total_active_pow"}}}
    ])

    # XGBoost depuis Django
    from django.db.models import Sum
    total_xgb_django = XGBoostPrediction.objects.aggregate(
        Sum('prediction_value')
    )['prediction_value__sum'] or 0

    # XGBoost depuis MongoDB (si existant)
    total_xgb_mongo = energy_db.xgb_predictions.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$total_active_pow"}}}
    ])

    total_lstm_value = next(total_lstm, {}).get('total', 0)
    total_xgb_mongo_value = next(total_xgb_mongo, {}).get('total', 0)
    total_xgb_value = total_xgb_django + total_xgb_mongo_value

    total_users = users_collection.count_documents({})
    outliers = energy_db.predicted_data.count_documents({"total_active_pow": {"$gt": 5000}})

    # Statistiques des prédictions
    total_predictions = XGBoostPrediction.objects.count()
    total_anomalies = 0  # À implémenter plus tard

    # ✅ Calcul du coût selon la grille tarifaire tunisienne
    cost_data = {}
    total_predicted_consumption = sum(xgb_values) if xgb_values else 0
    
    if total_predicted_consumption > 0:
        cost_data = calculate_tunisian_tariff(total_predicted_consumption)
        
        # Log du calcul dans la console du serveur
        logger.info('=== CALCUL DU COÛT DE LA CONSOMMATION PRÉDITE ===')
        logger.info(f'📊 Consommation totale prédite: {total_predicted_consumption:.2f} kWh')
        logger.info(f'💰 Coût hors TVA: {cost_data["costHT"]:.3f} DT')
        logger.info(f'📈 Montant TVA (19%): {cost_data["tva"]:.3f} DT')
        logger.info(f'🧾 Coût total TTC: {cost_data["costTTC"]:.3f} DT')
        logger.info('===============================================')

    return JsonResponse({
        "weekly_labels": sorted_dates,
        "real_values": real_values,
        "predicted_values": predicted_values,
        "xgb_values": xgb_values,  # Nouvelles données XGBoost
        "total_lstm": total_lstm_value,
        "total_xgb": total_xgb_value,
        "total_predictions": total_predictions,
        "total_anomalies": total_anomalies,
        "total_users": total_users,
        "outliers": outliers,
        "recent_files": recent_files,
        # ✅ Nouvelles données de coût
        "cost_data": cost_data,
        "total_predicted_consumption": total_predicted_consumption
    })
@login_required

def edit_profile(request):
    username = request.session.get('username')
    if not username:
        return redirect('/auth/login/')  # ou une autre page si tu l’as

    user = users_collection.find_one({'username': username})

    if request.method == 'POST':
        users_collection.update_one(
            {'username': username},
            {'$set': {
                'firstname': request.POST.get('firstname'),
                'lastname': request.POST.get('lastname'),
                'email': request.POST.get('email'),
                'phone': request.POST.get('phone'),
                'address': request.POST.get('address')
            }}
        )
        messages.success(request, "✅ Profil mis à jour avec succès.")
        return redirect('/auth/dashboard/')

    return render(request, 'edit_profile.html', {'user': user})


def edit_profile_advanced(request):
    """
    Vue avancée pour éditer le profil utilisateur avec upload de photo
    """
    username = request.session.get('username')
    if not username:
        messages.error(request, "❌ Vous devez être connecté pour accéder à cette page.")
        return redirect('login')

    user = users_collection.find_one({'username': username})
    if not user:
        messages.error(request, "❌ Utilisateur introuvable.")
        return redirect('login')

    # Vérifier si la photo existe
    import os
    from django.conf import settings

    photo_exists = False
    photo_url = None

    if user.get('photo_path'):
        # Vérifier si le fichier existe
        if os.path.exists(user['photo_path']):
            photo_exists = True
            # Construire l'URL relative pour l'affichage
            photo_filename = os.path.basename(user['photo_path'])
            photo_url = f"/static/faces/{photo_filename}"

    # Ajouter les informations de photo à l'objet user
    user['photo_exists'] = photo_exists
    user['photo_url'] = photo_url

    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            firstname = request.POST.get('firstname', '').strip()
            lastname = request.POST.get('lastname', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            address = request.POST.get('address', '').strip()
            new_username = request.POST.get('username', '').strip()

            # Validation des champs requis
            if not firstname or not lastname or not email or not new_username:
                messages.error(request, "❌ Les champs prénom, nom, email et nom d'utilisateur sont obligatoires.")
                return render(request, 'edit_profile.html', {'user': user})

            # Validation de l'email
            import re
            email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_regex, email):
                messages.error(request, "❌ Format d'email invalide.")
                return render(request, 'edit_profile.html', {'user': user})

            # Vérification si le nouveau nom d'utilisateur est disponible
            if new_username != username:
                existing_user = users_collection.find_one({'username': new_username})
                if existing_user:
                    messages.error(request, "❌ Ce nom d'utilisateur est déjà pris.")
                    return render(request, 'edit_profile.html', {'user': user})

            # Vérification si l'email est déjà utilisé par un autre utilisateur
            existing_email = users_collection.find_one({'email': email, 'username': {'$ne': username}})
            if existing_email:
                messages.error(request, "❌ Cette adresse email est déjà utilisée.")
                return render(request, 'edit_profile.html', {'user': user})

            # Gestion de l'upload de photo
            photo_path = user.get('photo_path', '')
            if 'photo' in request.FILES and request.FILES['photo']:
                photo_file = request.FILES['photo']

                # Validation du type de fichier
                allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
                file_type = photo_file.content_type.lower()
                if file_type not in allowed_types:
                    messages.error(request, f"❌ Format de fichier non supporté: {file_type}. Utilisez JPG, PNG ou GIF.")
                    return render(request, 'edit_profile.html', {'user': user})

                # Validation de la taille (max 5MB)
                if photo_file.size > 5 * 1024 * 1024:
                    size_mb = round(photo_file.size / (1024 * 1024), 2)
                    messages.error(request, f"❌ La taille du fichier ({size_mb}MB) dépasse la limite de 5MB.")
                    return render(request, 'edit_profile.html', {'user': user})

                # Sauvegarde de la photo
                import os
                from django.conf import settings

                # Créer le dossier faces s'il n'existe pas
                faces_dir = os.path.join(settings.STATICFILES_DIRS[0], 'faces')
                os.makedirs(faces_dir, exist_ok=True)

                # Déterminer l'extension du fichier
                file_extension = '.jpg'  # Par défaut JPG
                if 'png' in file_type:
                    file_extension = '.png'
                elif 'gif' in file_type:
                    file_extension = '.gif'

                # Nom du fichier
                photo_filename = f"{new_username}{file_extension}"
                photo_path = os.path.join(faces_dir, photo_filename)

                # Supprimer l'ancienne photo si elle existe
                old_photo_path = user.get('photo_path', '')
                if old_photo_path and os.path.exists(old_photo_path) and old_photo_path != photo_path:
                    try:
                        os.remove(old_photo_path)
                        logger.info(f"Ancienne photo supprimée: {old_photo_path}")
                    except Exception as e:
                        logger.warning(f"Impossible de supprimer l'ancienne photo: {e}")

                # Sauvegarder la nouvelle photo
                try:
                    with open(photo_path, 'wb+') as destination:
                        for chunk in photo_file.chunks():
                            destination.write(chunk)

                    logger.info(f"Nouvelle photo sauvegardée: {photo_path}")
                    messages.success(request, "📸 Photo de profil mise à jour avec succès !")

                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde de la photo: {e}")
                    messages.error(request, "❌ Erreur lors de la sauvegarde de la photo.")
                    return render(request, 'edit_profile.html', {'user': user})

            # Mise à jour des données utilisateur
            update_data = {
                'firstname': firstname,
                'lastname': lastname,
                'email': email,
                'phone': phone,
                'address': address,
                'username': new_username,
                'updated_at': datetime.now()
            }

            if photo_path:
                update_data['photo_path'] = photo_path

            # Mise à jour dans la base de données
            result = users_collection.update_one(
                {'username': username},
                {'$set': update_data}
            )

            if result.modified_count > 0:
                # Mise à jour de la session si le nom d'utilisateur a changé
                if new_username != username:
                    request.session['username'] = new_username

                messages.success(request, "✅ Profil mis à jour avec succès !")
                return redirect('dashboard')
            else:
                messages.warning(request, "⚠️ Aucune modification détectée.")

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du profil: {str(e)}")
            messages.error(request, "❌ Une erreur est survenue lors de la mise à jour.")

    return render(request, 'edit_profile.html', {'user': user})
def predict_xgb_view(request):
    """
    API endpoint AJAX pour lancer les prédictions XGBoost.
    Remplace toujours les prédictions existantes par de nouvelles.
    """
    from django.utils import timezone

    print("🚀 [DEBUG] === DÉBUT DE predict_xgb_view ===")

    # Vérifier l'authentification
    if not request.session.get('username'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': '❌ Vous devez être connecté pour lancer la prédiction.'
            }, status=401)
        else:
            return redirect('/?next=' + request.path)

    try:
        from ai_energy.utils.predict_xgboost import predict_next_30_days_xgb
        from pymongo import MongoClient
        import pandas as pd
        from datetime import datetime, timedelta

        # Connexion à MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db = client["energy_db"]
        
        # Calculer la période du mois suivant
        today = datetime.now()
        next_month_start = today + timedelta(days=1)
        next_month_end = next_month_start + timedelta(days=29)
        
        print(f"� [DEBUG] Remplacement des prédictions pour la période: {next_month_start.strftime('%Y-%m-%d')} à {next_month_end.strftime('%Y-%m-%d')}")
        
        # Charger les données historiques pour la prédiction
        daily_collection = db["daily_data"]
        data = list(daily_collection.find({}, {"_id": 0, "date": 1, "total_active_pow": 1}))
        if not data:
            return JsonResponse({
                'status': 'error',
                'message': '❌ Aucune donnée historique trouvée pour la prédiction.'
            }, status=400)
        
        df = pd.DataFrame(data)
        print(f"[DEBUG] {len(df)} lignes chargées depuis MongoDB pour la prédiction XGBoost.")

        # Appel de la fonction de prédiction (qui remplace automatiquement les anciennes prédictions)
        predict_next_30_days_xgb(df)

        response_data = {
            'status': 'success',
            'message': '✅ Prédictions remplacées et générées avec succès!',
            'predictions_count': 30,
            'period_start': next_month_start.strftime('%Y-%m-%d'),
            'period_end': next_month_end.strftime('%Y-%m-%d'),
            'replaced': True,
            'timestamp': str(timezone.now())
        }
        
        print(f"✅ [DEBUG] Réponse préparée: {response_data}")
        return JsonResponse(response_data)

    except Exception as e:
        print(f"❌ [DEBUG] Erreur dans predict_xgb_view: {str(e)}")
        import traceback
        print(f"❌ [DEBUG] Traceback: {traceback.format_exc()}")

        return JsonResponse({
            'status': 'error',
            'message': f'❌ Erreur lors de la génération des prédictions: {str(e)}'
        }, status=500)


def predict_xgb_page(request):
    """Page dédiée aux prédictions XGBoost"""
    # Charger les prédictions XGBoost depuis MongoDB
    xgb_predictions_mongo = list(energy_db.xgb_predictions.find().sort("date", 1))
    return render(request, 'predict_xgb_page.html', {
        'xgb_predictions_mongo': xgb_predictions_mongo
    })

def test_api(request):
    """Endpoint de test pour vérifier que l'API fonctionne"""
    from django.utils import timezone
    return JsonResponse({
        'status': 'success',
        'message': 'API fonctionne correctement',
        'timestamp': timezone.now().isoformat()
    })
def anomaly_detect_view(request):
    """
    Vue pour la page de détection d'anomalies
    """
    username = request.session.get('username')
    if not username:
        return redirect('login')

    # Récupérer les données d'anomalies depuis MongoDB
    try:
        from pymongo import MongoClient
        from datetime import datetime, timedelta
        import statistics

        client = MongoClient("mongodb://localhost:27017/")
        db = client["energy_db"]
        
        # Récupérer les données historiques
        daily_data = list(db.daily_data.find({}, {"total_active_pow": 1, "date": 1}).sort("date", -1).limit(100))
        
        anomalies = []
        mean_value = 0
        threshold = 0
        
        if daily_data:
            # Calculer les statistiques
            values = [d.get('total_active_pow', 0) for d in daily_data]
            mean_value = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            threshold = mean_value + (2 * std_dev)
            
            # Détecter les vraies anomalies seulement
            real_anomalies = []
            for data_point in daily_data:
                value = data_point.get('total_active_pow', 0)
                if value > threshold:
                    real_anomalies.append({
                        'date': data_point['date'].strftime('%Y-%m-%d'),
                        'value': round(value, 2),
                        'threshold': round(threshold, 2),
                        'deviation_percent': round(((value - mean_value) / mean_value) * 100, 2),
                        'severity': 'High' if value > threshold * 1.5 else 'Medium'
                    })
            
            # Trier par date décroissante
            anomalies = sorted(real_anomalies, key=lambda x: x['date'], reverse=True)
            
            # Log pour debug
            logger.info(f"Données analysées: {len(daily_data)} points")
            logger.info(f"Seuil calculé: {threshold:.2f}")
            logger.info(f"Anomalies détectées: {len(anomalies)}")
        else:
            # Aucune donnée dans la base
            logger.warning("Aucune donnée historique trouvée dans la base de données")
            anomalies = []
        
        # Statistiques d'anomalies
        stats = {
            'total_anomalies': len(anomalies),
            'high_severity': len([a for a in anomalies if a.get('severity') == 'High']),
            'medium_severity': len([a for a in anomalies if a.get('severity') == 'Medium']),
            'mean_consumption': round(mean_value, 2) if daily_data else 0,
            'threshold': round(threshold, 2) if daily_data else 0
        }
        
        return render(request, 'anomaly_detect.html', {
            'username': username,
            'anomalies': anomalies[:20],  # Limiter à 20 anomalies récentes
            'stats': stats,
            'photo_url': f'/static/faces/{username}.jpg' if os.path.exists(os.path.join(FACES_DIR, f'{username}.jpg')) else '/static/faces/default.jpg'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la détection d'anomalies: {str(e)}")
        return render(request, 'anomaly_detect.html', {
            'username': username,
            'error': 'Erreur lors de la récupération des données d\'anomalies.',
            'anomalies': [],
            'stats': {'total_anomalies': 0, 'high_severity': 0, 'medium_severity': 0}
        })
def anomaly_api(request):
    """
    API pour récupérer les données d'anomalies en JSON
    """
    try:
        from pymongo import MongoClient
        from datetime import datetime, timedelta
        import statistics

        client = MongoClient("mongodb://localhost:27017/")
        db = client["energy_db"]
        
        # Récupérer les données historiques
        daily_data = list(db.daily_data.find({}, {"total_active_pow": 1, "date": 1}).sort("date", -1).limit(100))
        
        anomalies = []
        mean_value = 0
        threshold = 0
        
        if daily_data:
            # Calculer les statistiques
            values = [d.get('total_active_pow', 0) for d in daily_data]
            mean_value = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            threshold = mean_value + (2 * std_dev)
            
            # Détecter les anomalies
            for data_point in daily_data:
                value = data_point.get('total_active_pow', 0)
                if value > threshold:
                    anomalies.append({
                        'date': data_point['date'].strftime('%Y-%m-%d'),
                        'value': round(value, 2),
                        'threshold': round(threshold, 2),
                        'deviation_percent': round(((value - mean_value) / mean_value) * 100, 2),
                        'severity': 'High' if value > threshold * 1.5 else 'Medium'
                    })
        
        # Trier par date décroissante
        anomalies = sorted(anomalies, key=lambda x: x['date'], reverse=True)
        
        return JsonResponse({
            'status': 'success',
            'anomalies': anomalies[:10],  # Top 10 anomalies
            'stats': {
                'total_anomalies': len(anomalies),
                'mean_consumption': round(mean_value, 2),
                'threshold': round(threshold, 2),
                'total_data_points': len(daily_data)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def image_upload_view(request):
    """
    Vue pour afficher la page d'upload d'images
    """
    username = request.session.get('username')
    if not username:
        return redirect('login')
    
    # Récupérer les prédictions récentes de l'utilisateur
    recent_predictions = UploadedImage.objects.filter(
        user_session=request.session.session_key or username
    )[:10]
    
    return render(request, 'image_upload.html', {
        'username': username,
        'recent_predictions': recent_predictions,
        'photo_url': f'/static/faces/{username}.jpg' if os.path.exists(os.path.join(FACES_DIR, f'{username}.jpg')) else '/static/faces/default.jpg'
    })

@csrf_exempt
def image_predict_api(request):
    """
    API pour uploader une image et obtenir une prédiction
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    username = request.session.get('username')
    if not username:
        return JsonResponse({'error': 'Non authentifié'}, status=401)
    
    try:
        # Vérifier la disponibilité du modèle
        if not predictor.is_model_available():
            return JsonResponse({
                'error': 'Modèle de prédiction non disponible',
                'status': 'error'
            }, status=500)
        
        # Vérifier qu'un fichier a été uploadé
        if 'image' not in request.FILES:
            return JsonResponse({
                'error': 'Aucune image fournie',
                'status': 'error'
            }, status=400)
        
        uploaded_file = request.FILES['image']
        
        # Valider le type de fichier
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
        if uploaded_file.content_type.lower() not in allowed_types:
            return JsonResponse({
                'error': f'Type de fichier non supporté: {uploaded_file.content_type}',
                'status': 'error'
            }, status=400)
        
        # Valider la taille (max 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            return JsonResponse({
                'error': 'Fichier trop volumineux (max 10MB)',
                'status': 'error'
            }, status=400)
        
        # Créer l'objet UploadedImage
        uploaded_image = UploadedImage()
        uploaded_image.image = uploaded_file
        uploaded_image.user_session = request.session.session_key or username
        uploaded_image.save()
        
        # Obtenir le chemin complet de l'image
        image_path = uploaded_image.image.path
        
        # Faire la prédiction
        prediction_result = predictor.predict(image_path)
        
        if 'error' in prediction_result:
            return JsonResponse({
                'error': prediction_result['error'],
                'status': 'error'
            }, status=500)
        
        # Mettre à jour l'objet avec les résultats
        uploaded_image.result_label = prediction_result['label']
        uploaded_image.confidence = prediction_result['confidence']
        uploaded_image.save()
        
        logger.info(f"🔍 Prédiction pour {username}: {prediction_result['label']} ({prediction_result['confidence']*100:.2f}%)")
        
        return JsonResponse({
            'status': 'success',
            'prediction': {
                'id': uploaded_image.id,
                'label': prediction_result['label'],
                'confidence': prediction_result['confidence'],
                'confidence_percentage': round(prediction_result['confidence'] * 100, 2),
                'is_anomaly': prediction_result['label'] == 'anomaly',
                'image_url': uploaded_image.image.url,
                'uploaded_at': uploaded_image.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la prédiction d'image: {str(e)}")
        return JsonResponse({
            'error': f'Erreur serveur: {str(e)}',
            'status': 'error'
        }, status=500)

def image_history_view(request):
    """
    Vue pour afficher l'historique des prédictions d'images
    """
    username = request.session.get('username')
    if not username:
        return redirect('login')
    
    # Récupérer toutes les prédictions de l'utilisateur
    all_predictions = UploadedImage.objects.filter(
        user_session=request.session.session_key or username
    )
    
    # Statistiques
    total_predictions = all_predictions.count()
    anomaly_count = all_predictions.filter(result_label='anomaly').count()
    good_count = all_predictions.filter(result_label='Good').count()
    
    stats = {
        'total': total_predictions,
        'anomalies': anomaly_count,
        'good': good_count,
        'anomaly_percentage': round((anomaly_count / total_predictions * 100), 2) if total_predictions > 0 else 0
    }
    
    return render(request, 'image_history.html', {
        'username': username,
        'predictions': all_predictions,
        'stats': stats,
        'photo_url': f'/static/faces/{username}.jpg' if os.path.exists(os.path.join(FACES_DIR, f'{username}.jpg')) else '/static/faces/default.jpg'
    })

@csrf_exempt
def delete_image_api(request, image_id):
    """
    API pour supprimer une image uploadée
    """
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    username = request.session.get('username')
    if not username:
        return JsonResponse({'error': 'Non authentifié'}, status=401)
    
    try:
        # Récupérer l'image
        uploaded_image = UploadedImage.objects.get(
            id=image_id,
            user_session=request.session.session_key or username
        )
        
        # Supprimer le fichier physique
        if uploaded_image.image and default_storage.exists(uploaded_image.image.name):
            default_storage.delete(uploaded_image.image.name)
        
        # Supprimer l'enregistrement
        uploaded_image.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Image supprimée avec succès'
        })
        
    except UploadedImage.DoesNotExist:
        return JsonResponse({
            'error': 'Image non trouvée',
            'status': 'error'
        }, status=404)
    except Exception as e:
        logger.error(f"❌ Erreur lors de la suppression: {str(e)}")
        return JsonResponse({
            'error': f'Erreur serveur: {str(e)}',
            'status': 'error'
        }, status=500)