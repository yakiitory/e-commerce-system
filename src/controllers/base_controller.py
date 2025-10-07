from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")
ID = TypeVar("ID", bound=int)

class BaseController(ABC, Generic[T, ID]):
    """Contract for every controller to follow"""

    @abstractmethod
    def create(self, data: T) -> T | None: ...

    @abstractmethod
    def read(self, identifier: ID) -> T | None: ...

    @abstractmethod
    def update(self, identifier: ID, data: T) -> T | None: ...

    @abstractmethod
    def delete(self, identifier: ID) -> bool: ...


