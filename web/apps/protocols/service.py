from ulid import ULID
from asgiref.sync import sync_to_async

from .models import Protocol


@sync_to_async
def get_patient_uild(doctor_id: str, patient_name: str) -> str:
    doctor_patient_protocols = list(Protocol.objects.filter(
        doctor_id=doctor_id,
        patient_name=patient_name
    ))
    if doctor_patient_protocols:
        patient_ulid = doctor_patient_protocols[0].patient_ulid
    else: 
        patient_ulid = str(ULID())
        
    return patient_ulid