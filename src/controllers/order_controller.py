from typing import override
from controllers.base_controller import BaseController
from ..models.orders import Order
from ..models.mixins import ID

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
