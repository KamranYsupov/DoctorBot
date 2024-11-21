from django.contrib import admin

from .models import Protocol


@admin.register(Protocol)
class ProtocolAdmin(admin.ModelAdmin):
    """Админ-панель для управления протоколами"""
    list_display = (
        'id',
        'patient_name',
        'doctor_fio',
        'time_to_take',
        'period',
    )
    list_display_links = (
        'id',
        'patient_name',
        'doctor_fio',
    )
    readonly_fields = ('patient_name', )
    excluded_fields = (
        'reception_calendar',
        'notifications_calendar'
    )
    search_fields = (
        'telegram_id', 
        'patient_name__iregex', 
        'doctor__fio__iregex',
    )
    
    @admin.display(description='ФИО доктора',)
    def doctor_fio(self, obj):
        return obj.doctor.fio
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        return []
    

    
    def get_exclude(self, request, obj=None):
        # Если объект уже существует (редактирование), то исключаем поля field1 и field3
        if obj:
            return self.excluded_fields
        return ()

