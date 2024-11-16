from datetime import datetime, timedelta


def get_timedelta_calendar(first_take: datetime, period: int) -> dict:    
    timedelta_calendar = {}
    
    for day in range(period+1):
        take = first_take + timedelta(days=day)
        timedelta_calendar[take.strftime('%d.%m.%Y')] = False
        
    return timedelta_calendar