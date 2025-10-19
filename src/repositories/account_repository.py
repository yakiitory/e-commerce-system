from typing import Generic, override

from repositories.base_repository import BaseRepository
from ..models.accounts import User, Merchant, Admin
from ..models.mixins import T, ID


"""Any usage of a List[Int] is for indexing in the database."""


class AccountRepository(BaseRepository[T, ID], Generic[T, ID]):
    @override
    def save(self, data: T) -> T | None:
        return

    @override
    def find_by_id(self, id: ID) -> T | None: ...

    @override
    def delete(self, id: ID) -> bool: ... 


class UserRepository(AccountRepository[User, ID]):
    @override
    def save(self, data: User) -> User | None:
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
    def save(self, data: Merchant) -> Merchant | None:
        return


    @override
    def find_by_id(self, id: ID) -> Merchant | None:
        return


    @override
    def delete(self, id: ID) -> bool:
        return True


class AdminRepository(AccountRepository[Admin, ID]):
    @override
    def save(self, data: Admin) -> Admin | None:
        return


    @override
    def find_by_id(self, id: ID) -> Admin | None:
        return


    @override
    def delete(self, id: ID) -> bool:
        return True
