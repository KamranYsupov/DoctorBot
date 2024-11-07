from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.model_mixins import AbstractTelegramUser


class Patient(AbstractTelegramUser):
    name = models.CharField(_('Имя'), max_length=150)
    
    class Meta:
        verbose_name = _('Пациент')
        verbose_name_plural = _('Пациенты')
        
    def __str__(self):
        return self.name
