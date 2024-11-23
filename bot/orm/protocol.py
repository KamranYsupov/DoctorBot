from typing import List

from asgiref.sync import sync_to_async

from web.protocols.models import Protocol
from web.patients.models import Patient


@sync_to_async
def get_patients_names_by_doctor_id(doctor_id: int) -> List[str]:
    patients_names = set(
        Protocol.objects
        .filter(doctor_id=doctor_id)
        .select_related('patient', 'doctor')
        .values_list('patient_name', flat=True)
    )
    
    
    
    return list(patients_names)