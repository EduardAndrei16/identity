from django.contrib import admin
from .models import Application

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'app_type', 'owner', 'status', 'created_at')
    list_filter = ('app_type', 'status')
    search_fields = ('name', 'owner__username', 'owner__email')
    readonly_fields = ('created_at', 'updated_at')