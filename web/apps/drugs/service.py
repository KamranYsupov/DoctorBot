from typing import List

from django.utils import timezone

from .models import Drug


def get_unnotificated_drugs() -> List[Drug]:
    now = timezone.now()
    current_drugs = Drug.objects.select_related(
        'protocol',
        'protocol__patient',
        'protocol__doctor'
    ).filter(
        first_take__lte=now.date(),
        last_take__gte=now.date(),
        protocol__patient__isnull=False,
    )
    current_date_strformat = now.strftime('%d.%m.%Y')
    
    unnotificated_drugs = [
        drug for drug in current_drugs
        if drug.notifications_calendar.get(current_date_strformat) == False
    ]
    
    return unnotificated_drugs