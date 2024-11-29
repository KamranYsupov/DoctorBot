from django.contrib import admin

from .models import Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    """Админ-панель для управления докторами"""
    list_display = ('fio',  'username', 'telegram_id',)
    search_fields = (
        'telegram_id',
        'username__icontains',  
        'fio___icontains', 
    )
