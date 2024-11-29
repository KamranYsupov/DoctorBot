from uuid import UUID
from typing import List

from asgiref.sync import sync_to_async
from django.db import transaction

from schemas.patient import PatientCreateSchema
from models import Patient, Doctor, Protocol


@sync_to_async
def get_or_create_patient_and_update_protocol(
    protocol: Protocol, 
    patient_schema: PatientCreateSchema
) -> Patient:
    with transaction.atomic():
        patient, is_created = Patient.objects.get_or_create(
            telegram_id=patient_schema.telegram_id,
            defaults=patient_schema.model_dump()
        )
        protocol.patient = patient
        protocol.save()
        
        return patient
    
    
@sync_to_async
def get_patient_doctors(patient_id: str) -> List[Doctor]:
    doctor_ids = (
        Protocol.objects.filter(patient_id=patient_id)
        .select_related('patient', 'doctor')
        .values_list('doctor_id', flat=True)
    )
    doctors = Doctor.objects.filter(id__in=doctor_ids)
    
    return list(doctors)
    