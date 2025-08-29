from django.urls import path
from . import views
from ai_energy import views as energy_views

urlpatterns = [
    path('', views.login_view, name='login'),  
    path('register/', views.register, name='face_register'),
    path('success/', views.success, name='face_success'),
    path('upload/', views.upload_view, name='upload'),  
    path('analyse-csv/', energy_views.analyse_csv, name='analyse_csv'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('api/stats/', views.stats_api, name='stats_api'),
    path('verify-email/<str:username>/', views.verify_email, name='verify_email'),
    path('resend-verification-code/<str:username>/', views.resend_verification_code, name='resend_verification_code'),
    path('api/consommation/', views.consommation_jour, name='consommation_jour'),
    path('profile/edit/', views.edit_profile_advanced, name='edit_profile'),
    path('predict-xgb/', views.predict_xgb_view, name='predict_xgb'),
    path('predict-xgb-page/', views.predict_xgb_page, name='predict_xgb_page'),
    path('anomaly-detect/', views.anomaly_detect_view, name='anomaly_detect'),
    path('api/anomalies/', views.anomaly_api, name='anomaly_api'),
    path('test-api/', views.test_api, name='test_api'),
    
    # Image prediction URLs
    path('image-upload/', views.image_upload_view, name='image_upload'),
    path('api/image-predict/', views.image_predict_api, name='image_predict_api'),
    path('image-history/', views.image_history_view, name='image_history'),
    path('api/image-delete/<int:image_id>/', views.delete_image_api, name='delete_image_api'),

]
