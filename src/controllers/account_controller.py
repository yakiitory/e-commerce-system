from typing import override, TypeVar, Generic
from controllers.base_controller import ID, BaseController, T
from abc import ABC, abstractmethod

from models.accounts import User, Merchant, Admin


# TODO: This is all just placeholder.
# TODO: Implement all of the features here
class AccountController(BaseController[T, ID], Generic[T, ID]):
    @override
    def create(self, data: T) -> T | None:
        return

    @override
    def read(self, identifier: int) -> T | None:
        return

    @override
    def update(self, identifier: int, data: T ) -> T | None:
        return

    @override
    def delete(self, identifier: int) -> bool:
        return True



class UserController(AccountController[User, ID]):
    @override
    def create(self, data: User) -> User | None:
        return super().create(data)


    @override
    def read(self, identifier: int) -> User | None:
        return super().read(identifier)


    @override
    def update(self, identifier: int, data: User) -> User | None:
        return super().update(identifier, data)


    @override
    def delete(self, identifier: int) -> bool:
        return super().delete(identifier)


class MerchantController(AccountController[Merchant, ID]):
    @override
    def create(self, data: Merchant) -> Merchant | None:
        return super().create(data)


    @override
    def read(self, identifier: int) -> Merchant | None:
        return super().read(identifier)


    @override
    def update(self, identifier: int, data: Merchant) -> Merchant | None:
        return super().update(identifier, data)


    @override
    def delete(self, identifier: int) -> bool:
        return super().delete(identifier)


class AdminController(AccountController[Admin, ID]):
    @override
    def create(self, data: Admin) -> Admin | None:
        return super().create(data)


    @override
    def read(self, identifier: int) -> Admin | None:
        return super().read(identifier)


    @override
    def update(self, identifier: int, data: Admin) -> Admin | None:
        return super().update(identifier, data)


    @override
    def delete(self, identifier: int) -> bool:
        return super().delete(identifier)
