from typing import override
from controllers.base_controller import ID, BaseController
from ..models.orders import Order

class OrderController(BaseController[Order, ID]):
    @override
    def create(self, data: Order) -> Order | None:
        return


    @override
    def read(self, identifier: ID) -> Order | None:
        return


    @override
    def update(self, identifier: ID, data: Order) -> Order | None:
        return


    @override
    def delete(self, identifier: ID) -> bool:
        return True
