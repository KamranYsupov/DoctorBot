from typing import Sequence, List, Dict

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
    def a_all(
        self,
        select_relations: Sequence[str] = [],
        prefetch_relations: Sequence[str] = [],
    ) -> List:
        return list(
            super()
            .select_related(*select_relations)
            .prefetch_related(*prefetch_relations)
        )
    
    @sync_to_async
    def afilter(
        self,
        select_relations: Sequence[str] = [],
        prefetch_relations: Sequence[str] = [],
        **kwargs
    ) -> List:
        return list(
            super()
            .filter(**kwargs)
            .select_related(*select_relations)
            .prefetch_related(*prefetch_relations)
        )
    
    @sync_to_async
    def aget_or_create(self, defaults: Dict = {}, **kwargs):
        return super().get_or_create(defaults, **kwargs)