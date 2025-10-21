from abc import ABC, abstractmethod

class BaseController(ABC):
    """Contract for every controller to follow"""

    @abstractmethod
    def create(self, data): ...

    @abstractmethod
    def read(self, identifier): ...

    @abstractmethod
    def update(self, identifier, data): ...

    @abstractmethod
    def delete(self, identifier): ...


