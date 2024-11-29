from django.contrib import admin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """Админ-панель для управления пациентами"""
    list_display = ('name',  'username', 'telegram_id', 'phone_number')
    search_fields = (
        'telegram_id', 
        'username__icontains', 
        'name__icontains',
        'phone_number'
    )
