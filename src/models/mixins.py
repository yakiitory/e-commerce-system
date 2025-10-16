from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar

T = TypeVar("T")
ID = TypeVar("ID", bound=int)


@dataclass
class AuthMixin:
    username: str
    hash: str
    last_login: datetime
    is_active: bool 


@dataclass
class ContactMixin:
    first_name: str
    last_name: str
    phone_number: str
    email: str


@dataclass
class DateMixin:
    created_at: datetime
