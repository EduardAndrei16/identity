from django.db import models
from django.contrib.auth.models import User

class Application(models.Model):
    APP_TYPE_CHOICES = [
        ('SAML', 'SAML'),
        ('OIDC', 'OIDC'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('error', 'Error'),
    ]
    
    name = models.CharField(max_length=255)
    app_type = models.CharField(max_length=10, choices=APP_TYPE_CHOICES)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # SAML specific fields
    saml_sso_url = models.URLField(blank=True, null=True)
    saml_entity_id = models.CharField(max_length=255, blank=True, null=True)
    saml_relay_state = models.CharField(max_length=255, blank=True, null=True)
    saml_username_template = models.CharField(max_length=50, blank=True, null=True)
    
    # OIDC specific fields
    oidc_client_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Common fields
    passport_policies = models.TextField(blank=True, null=True)
    configuration_data = models.JSONField(blank=True, null=True)  # Store additional configuration
    
    def __str__(self):
        return f"{self.name} ({self.app_type})"