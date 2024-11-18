from django.db import models
from asgiref.sync import sync_to_async


class AsyncBaseManager(models.Manager):
    """Базовый асинхронный менеджер модели"""
    @sync_to_async
    def aget(self, *args, **kwargs):
        return super().get(*args, **kwargs)
    
    @sync_to_async
    def acreate(self, **kwargs):
        return super().create(**kwargs)
    
    @sync_to_async
    def a_all(self):
        return super().all()
    
    @sync_to_async
    def afilter(self, *args, **kwargs):
        return super().filter(*args, **kwargs)
    
    @sync_to_async
    def aget_or_create(self, defaults: dict = {}, **kwargs):
        return get_or_create().get_or_create(defaults, **kwargs)