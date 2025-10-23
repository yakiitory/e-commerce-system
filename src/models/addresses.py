from dataclasses import dataclass

@dataclass
class AddressCreate():
    house_no: str
    street: str
    city: str
    postal_code: str
    additional_notes: str

@dataclass
class Address(AddressCreate):
    id: int
