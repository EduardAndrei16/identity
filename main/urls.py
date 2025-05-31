from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('app_onboarding/', views.app_onboarding, name='app_onboarding'),
    path('auth_clients/', views.auth_clients, name='auth_clients'),
    path('audits_reports/', views.audits_reports, name='audits_reports'),
    path('app_update/', views.app_update, name='app_update'),
    
    # Authentication URLs
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('oauth2/callback/', views.oauth2_callback, name='oauth2_callback'),
    path('api/auth/callback', views.auth_callback_api, name='auth_callback_api'),
]