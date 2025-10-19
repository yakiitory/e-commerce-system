from abc import ABC, abstractmethod
from typing import Generic
from ..models.mixins import T, ID


class BaseRepository(ABC, Generic[T, ID]):
    @abstractmethod
    def save(self, data: T) -> T | None: ...

    @abstractmethod
    def find_by_id(self, id: ID) -> T | None: ...

    @abstractmethod
    def delete(self, id: ID) -> bool: ...



