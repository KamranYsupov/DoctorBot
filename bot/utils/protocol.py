from datetime import datetime, timedelta

from aiogram.fsm.context import FSMContext

from web.protocols.models import Protocol


def get_timedelta_calendar(first_take: datetime, period: int) -> dict:    
    timedelta_calendar = {}
    
    for day in range(period+1):
        take = first_take + timedelta(days=day)
        timedelta_calendar[take.strftime('%d.%m.%Y')] = False
        
    return timedelta_calendar


async def get_protocol_from_state(state: FSMContext) -> Protocol:
    state_data = await state.get_data()
    protocol_id = int(state_data.get('protocol_id'))
    
    return await Protocol.objects.aget(id=protocol_id)