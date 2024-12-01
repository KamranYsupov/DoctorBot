from typing import List

from asgiref.sync import sync_to_async
from django.db import transaction

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
def get_patients_names_by_doctor_id(doctor_id: int) -> List[str]:
    patients_names = set(
        Protocol.objects
        .filter(doctor_id=doctor_id)
        .select_related('patient', 'doctor')
        .values_list('patient_name', flat=True)
    )
    
    
    
    return list(patients_names)