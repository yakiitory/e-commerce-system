from abc import ABC, abstractmethod
from database.database import Database

class BaseService(ABC):
    """Contract for every service to follow"""

    @abstractmethod
    def create(self, data): ...

    @abstractmethod
    def read(self, identifier): ...

    @abstractmethod
    def update(self, identifier, data): ...

    @abstractmethod
    def delete(self, identifier): ...