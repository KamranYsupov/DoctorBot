from django.contrib import admin

from .models import Protocol


@admin.register(Protocol)
class ProtocolAdmin(admin.ModelAdmin):
    """Админ-панель для управления протоколами"""
    list_display = (
        'id',
        'patient_name',
        'doctor_fio',
    )
    list_display_links = (
        'id',
        'patient_name',
        'doctor_fio',
    )
    readonly_fields = ('patient_name', )
    search_fields = (
        'patient_name__icontains', 
        'doctor__fio__icontains',
    )
    
    @admin.display(description='ФИО доктора',)
    def doctor_fio(self, obj):
        return obj.doctor.fio
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        return []


