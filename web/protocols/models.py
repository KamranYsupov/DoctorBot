from django.db import models
from django.utils.translation import gettext_lazy as _

from web.utils.base_manager import AsyncBaseManager


class Protocol(models.Model):
    drugs = models.ManyToManyField(
        'drugs.Drug', 
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
    
    
