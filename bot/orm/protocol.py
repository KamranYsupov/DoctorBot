from uuid import UUID
from typing import List, Tuple

from asgiref.sync import sync_to_async
from django.db import transaction
from ulid import ULID

from schemas.protocol import ProtocolCreateSchema
from web.protocols.models import Protocol
from web.patients.models import Patient
from web.drugs.models import Drug


@sync_to_async
def create_protocol_and_set_drugs(
    schema: ProtocolCreateSchema,
) -> Protocol:
    protocol_data = schema.model_dump()
    drugs_data = protocol_data.pop('drugs')
    with transaction.atomic():
        protocol = Protocol.objects.create(**protocol_data)
        created_drugs = Drug.objects.bulk_create(
            [
                Drug(protocol_id=protocol.id, **drug_data) 
                for drug_data in drugs_data
            ],
            batch_size=1000,
        )

    return protocol


@sync_to_async
def get_patient_names_and_ulids_by_doctor_id(
    doctor_id: str
) -> List[Tuple[str, str]]:
    patient_names_and_ulids = set(
        Protocol.objects
        .filter(doctor_id=doctor_id)
        .select_related('patient', 'doctor')
        .values_list('patient_name', 'patient_ulid')
    )
    
    return list(patient_names_and_ulids)


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