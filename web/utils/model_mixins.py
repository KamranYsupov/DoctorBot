from django.db import models
from django.utils.translation import gettext_lazy as _


class AbstractTelegramUser(models.Model):
    telegram_id = models.BigIntegerField(
        verbose_name=_('Телеграм ID'),
        unique=True,
        db_index=True,
        null=True,
    )
    username = models.CharField(_('Имя пользователя'), max_length=70)
    
    class Meta: 
        abstract = True