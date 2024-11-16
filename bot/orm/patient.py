from asgiref.sync import sync_to_async
from django.db.transaction import atomic

from schemas.patient import PatientCreateSchema
from web.protocols.models import Protocol
from web.patients.models import Patient


@sync_to_async
def get_or_create_patient_and_update_protocol(
    protocol: Protocol, 
    patient_schema: PatientCreateSchema
) -> Patient:
    with atomic():
        patient, is_created = Patient.objects.get_or_create(
            telegram_id=patient_schema.telegram_id,
            defaults=patient_schema.model_dump()
        )
        protocol.patient = patient
        protocol.save()
        
        return patient
    