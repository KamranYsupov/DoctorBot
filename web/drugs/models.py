from django.db import models
from django.utils.translation import gettext_lazy as _

from web.utils.base_manager import AsyncBaseManager


class Drug(models.Model):
    name = models.CharField(
        _('Название'), 
        db_index=True,
        max_length=150
    )
    first_take = models.DateField(
        _('День первого приема'),
        auto_now=False,
        auto_now_add=False
    )
    last_take = models.DateField(
        _('День последнего приема'),
        db_index=True,
        auto_now=False,
        auto_now_add=False
    )
    time_to_take = models.TimeField(
        _('Время приема'),
        auto_now=False,
        auto_now_add=False
    )
    reception_calendar = models.JSONField(
        _('Календарь према препаратов'),
        default=dict
    )
    notifications_calendar = models.JSONField(
        _('Календарь для проверки отправки уведомлений'),
        default=dict
    )
    
    protocol = models.ForeignKey(
        'protocols.Protocol',
        verbose_name=_('Протокол'),
        related_name='drugs',
        on_delete=models.CASCADE
    )

    objects = AsyncBaseManager()

    class Meta:
        verbose_name = _('Препарат')
        verbose_name_plural = _('Препараты')

    def __str__(self):
        return self.name
    
    @property
    def period(self) -> int:
        delta = self.last_take - self.first_take
        
        return delta.days
