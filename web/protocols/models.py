from django.db import models
from django.utils.translation import gettext_lazy as _

from web.utils.base_manager import AsyncBaseManager


class Drug(models.Model):
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


class Protocol(models.Model):
    drugs = models.ManyToManyField(
        Drug, 
        related_name='protocols',
        verbose_name=_('Препараты'), 
    )
    patient_name = models.CharField(
        _('Имя пациента'), 
        db_index=True,
        max_length=150
    )
    doctor = models.ForeignKey(
        'doctors.Doctor',
        verbose_name=_('Доктор'),
        related_name='protocols',
        db_index=True,
        on_delete=models.CASCADE,
    )
    patient = models.ForeignKey(
        'patients.Patient',
        verbose_name=_('Пациент'),
        related_name='protocols',
        db_index=True,
        on_delete=models.CASCADE,
        null=True,
        default=None,
    )
    
    objects = AsyncBaseManager()

    class Meta:
        verbose_name = _('Протокол')
        verbose_name_plural = _('Протоколы')

    def __str__(self):
        return f'ID {self.id} | {self.patient_name}'
    
    
