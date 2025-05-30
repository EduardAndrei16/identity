from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('app_onboarding/', views.app_onboarding, name='app_onboarding'),
    
    # Authentication URLs
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('oauth2/callback/', views.oauth2_callback, name='oauth2_callback'),
    path('api/auth/callback', views.auth_callback_api, name='auth_callback_api'),
]