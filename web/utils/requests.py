from typing import Callable
from functools import wraps

import requests


def send_request_until_success(
    send_request_method: Callable
):
    @wraps(send_request_method)
    def wrapper(*args, **kwargs):
        status_code = 1
        
        while status_code != 200:
            try:
                response = send_request_method(*args, **kwargs)
            except requests.exceptions.ConnectTimeout:
                continue
        
            status_code = response.status_code
    
        return response
    
    return wrapper