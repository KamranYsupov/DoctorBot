from django.db import models
from asgiref.sync import sync_to_async


class AsyncBaseManager(models.Manager):
    """Базовый асинхронный менеджер модели"""
    @sync_to_async
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)
    
    @sync_to_async
    def create(self, **kwargs):
        return super().create(**kwargs)
    
    @sync_to_async
    def all(self):
        return super().all()
    
    @sync_to_async
    def filter(self, *args, **kwargs):
        return super().filter(*args, **kwargs)