from dataclasses import dataclass
from datetime import datetime

@dataclass
class AuthMixin:
    username: str
    hash: str
    last_login: datetime
    is_active: datetime


@dataclass
class ContactMixin:
    first_name: str
    last_name: str
    phone_number: str
    email: str

    
@dataclass
class DateMixin:
    created_at: datetime
    


