from abc import ABC, abstractmethod
from ..models.mixins import T, ID

class BaseRepository(ABC):
    @abstractmethod
    def save(self, data: T) -> T | None: ...

    @abstractmethod
    def find_by_id(self, id: ID) -> T | None: ...

    @abstractmethod
    def delete(self, id: ID) -> bool: ...



