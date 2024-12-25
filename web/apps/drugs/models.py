from datetime import timedelta

from django.db import models
from django.utils.translation import gettext_lazy as _
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
            timedelta_calendar = {}
            
            for day in range(self.period+1):
                take = self.first_take + timedelta(days=day)
                take_strformat = take.strftime(settigs.DEFAULT_DATE_FORMAT)
                
                timedelta_calendar[take_strformat] = None
                
            sorted_timedelta_calendar = dict(
                sorted(
                    timedelta_calendar.items(), 
                    key=lambda item: datetime.strptime(
                        item[0], settigs.DEFAULT_DATE_FORMAT
                    ))
            )
            self.reception_calendar = sorted_timedelta_calendar
            self.notifications_calendar = sorted_timedelta_calendar
            
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    @property
    def period(self) -> int:
        delta = self.last_take - self.first_take
        
        return delta.days
