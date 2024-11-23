from typing import Optional, Union

from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist

from web.patients.models import Patient
from web.doctors.models import Doctor


@sync_to_async
def get_doctor_or_patient(
    telegram_id: int, 
) -> Optional[Union[Doctor, Patient]]:
    try:
        doctor = Doctor.objects.get(telegram_id=telegram_id)
        return doctor
        
    except ObjectDoesNotExist:
        pass
    
    try:
        patient = Patient.objects.get(telegram_id=telegram_id)
        return patient
        
    except ObjectDoesNotExist:
        pass
    

    
    