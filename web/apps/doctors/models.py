from django.db import models
from django.utils.translation import gettext_lazy as _

from web.db.model_mixins import AbstractTelegramUser


class Doctor(AbstractTelegramUser):
    fio = models.CharField(_('ФИО'), max_length=150)

    class Meta:
        verbose_name = _('Доктор')
        verbose_name_plural = _('Доктора')
        
    def __str__(self):
        return self.fio