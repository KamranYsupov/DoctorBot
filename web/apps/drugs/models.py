from datetime import timedelta, datetime

import loguru
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

from web.db.base_manager import AsyncBaseManager
from web.db.model_mixins import AsyncBaseModel


class Drug(AsyncBaseModel):
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
        ordering = ['time_to_take']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__first_take = self.first_take
        self.__last_take = self.last_take
    
    def save(self, *args, **kwargs):
        if (
            self.__first_take != self.first_take or
            self.__last_take != self.last_take
        ):   
            updated_reception_calendar = {}
            updated_notifications_calendar = {}
            
            for day in range(self.period+1):
                take = self.first_take + timedelta(days=day)
                take_strformat = take.strftime(settings.DEFAULT_DATE_FORMAT)
                
                updated_reception_calendar[take_strformat] = \
                    self.reception_calendar.get(take_strformat)
                
                updated_notifications_calendar[take_strformat] = \
                    self.notifications_calendar.get(take_strformat)
                    
            self.reception_calendar = updated_reception_calendar
            self.notifications_calendar = updated_notifications_calendar
            

        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    @property
    def period(self) -> int:
        delta = self.last_take - self.first_take
        
        return delta.days
    
    
    def is_available_to_notify(self, day: datetime) -> bool:
        current_date_strformat = day.strftime(settings.DEFAULT_DATE_FORMAT)
        
        try:
            self.reception_calendar[current_date_strformat] 
        except KeyError:
            return False
    
        if self.reception_calendar[current_date_strformat]:
            return False
        
        return True
