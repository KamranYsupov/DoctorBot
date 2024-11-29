from django.apps import AppConfig


class DoctorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web.apps.doctors'
    verbose_name = 'Управление докторами'