from enum import Enum

class Status(Enum):
    PENDING = 1
    PAID = 2
    SHIPPED = 3
    DELIVERED = 4
    CANCELLED = 5
    REFUNDED = 6
    RETURNED = 7

