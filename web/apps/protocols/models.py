from ulid import ULID
import loguru

from django.db import models
from django.utils.translation import gettext_lazy as _

from web.db.base_manager import AsyncBaseManager
from web.db.model_mixins import AsyncBaseModel, TimestampMixin


class Protocol(AsyncBaseModel, TimestampMixin):
    patient_name = models.CharField(
        _('ФИО пациента'), 
        max_length=150
    )
    patient_ulid = models.CharField( 
        # id пациета, нужно для callback_data в меню бота, 
        # т. к. ForeignKey поле patient заполняется при переходе  
        # по qr-коду после создания протокола 
        max_length=26,
        db_index=True,
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
        ordering = ['-created_at']

    def __str__(self):
        return f'ID {self.id} | {self.patient_name}'
    
    def save(self, *args, **kwargs):
        if self.patient_ulid:
            return super().save(*args, **kwargs)
                        
        doctor_patient_protocols = list(
            Protocol.objects.filter(
                doctor_id=self.doctor_id,
                patient_name=self.patient_name
            )
        )
        if doctor_patient_protocols:
            self.patient_ulid = doctor_patient_protocols[0].patient_ulid
        else: 
            self.patient_ulid = str(ULID())
            
        return super().save(*args, **kwargs)
        
    
    
