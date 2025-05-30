from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('accounts/', include(("okta_oauth2.urls", "okta_oauth2"), namespace="okta_oauth2")),
]