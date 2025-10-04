from dataclasses import dataclass

@dataclass
class Address():
    house_no: str
    street: str
    city: str
    postal_code: str
    additional_notes: str
