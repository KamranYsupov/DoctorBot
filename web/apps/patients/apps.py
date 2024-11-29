from django.apps import AppConfig


class PatientsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web.apps.patients'
    verbose_name = 'Управление пациентами'
