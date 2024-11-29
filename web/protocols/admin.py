from django.contrib import admin

from web.drugs.models import Drug
from .models import Protocol


class DrugInline(admin.TabularInline):
    model = Drug
    extra = 1


@admin.register(Protocol)
class ProtocolAdmin(admin.ModelAdmin):
    """Админ-панель для управления протоколами"""
    list_display = (
        'id',
        'patient_name',
        'doctor_fio',
        'display_drugs'
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
    
    inlines = (DrugInline, )
        
    @admin.display(description='ФИО доктора',)
    def doctor_fio(self, obj):
        return obj.doctor.fio
    
    @admin.display(description='Препараты',)
    def display_drugs(self, obj):
        return ', '.join([drug.name for drug in obj.drugs.all()])

    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        return []


