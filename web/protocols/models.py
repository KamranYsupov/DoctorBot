from django.db import models
from django.utils.translation import gettext_lazy as _

from web.utils.base_manager import AsyncBaseManager


class Protocol(models.Model):
    drugs = models.JSONField(_('Список препаратов'), default=list())
    patient_name = models.CharField(_('Имя пациента'), max_length=150)
    first_take = models.DateField(
        _('День первого приема'),
        auto_now=False,
        auto_now_add=False
    )
    period = models.IntegerField(_('Число дней приема'))
    time_to_take = models.TimeField(
        _('Время приема'),
        auto_now=False,
        auto_now_add=False
    )
    
    doctor = models.ForeignKey(
        'doctors.Doctor',
        verbose_name=_('Доктор'),
        related_name='protocols',
        on_delete=models.CASCADE,
    )
    patient = models.ForeignKey(
        'patients.Patient',
        verbose_name=_('Пациент'),
        related_name='protocols',
        on_delete=models.CASCADE,
        null=True,
        default=None,
    )
    
    objects = AsyncBaseManager()

    class Meta:
        verbose_name = _('Протокол')
        verbose_name_plural = _('Протоколы')

    def __str__(self):
        return self.patient_name
