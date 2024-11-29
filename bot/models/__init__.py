__all__ = (
    'Patient',
    'Doctor',
    'Protocol',
    'Drug'
)

from web.apps.patients.models import Patient
from web.apps.doctors.models import Doctor
from web.apps.protocols.models import Protocol
from web.apps.drugs.models import Drug