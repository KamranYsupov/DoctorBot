from django.db import models
from django.utils.translation import gettext_lazy as _

from web.db.model_mixins import AbstractTelegramUser


class Patient(AbstractTelegramUser):
    name = models.CharField(_('ФИО'), max_length=35)
    phone_number = models.CharField(
        _('Номер телефона'),
        max_length=50,
        unique=True,
    )
    
    class Meta:
        verbose_name = _('Пациент')
        verbose_name_plural = _('Пациенты')
        
    def __str__(self):
        return self.name
