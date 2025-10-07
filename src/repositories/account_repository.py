from abc import ABC, abstractmethod
from typing import Generic, TypeVar, override
from ..models.accounts import Account, User, Merchant, Admin

"""Any usage of a List[Int] is for indexing in the database."""


T = TypeVar("T", bound=Account)
ID = TypeVar("ID", bound=int)


class AccountRepository(ABC, Generic[T, ID]):
    @abstractmethod
    def save(self, account: T) -> T | None: ...

    @abstractmethod
    def find_by_id(self, id: ID) -> T | None: ...

    @abstractmethod
    def delete(self, id: ID) -> bool: ... 


class UserRepository(AccountRepository[User, ID]):
    @override
    def save(self, account: User) -> User | None:
    #TODO: DB Logic for UserRepository
        return


    @override
    def find_by_id(self, id: ID) -> User | None:
        return


    @override
    def delete(self, id: ID) -> bool:
        return True

    """User specific methods"""
    # TODO: Implement ^


class MerchantRepository(AccountRepository[Merchant, ID]):
    @override
    def save(self, account: Merchant) -> Merchant | None:
        return


    @override
    def find_by_id(self, id: ID) -> Merchant | None:
        return


    @override
    def delete(self, id: ID) -> bool:
        return True


class AdminRepository(AccountRepository[Admin, ID]):
    @override
    def save(self, account: Admin) -> Admin | None:
        return


    @override
    def find_by_id(self, id: ID) -> Admin | None:
        return


    @override
    def delete(self, id: ID) -> bool:
        return True
