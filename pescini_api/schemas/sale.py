from typing import Any, Dict

from pydantic import BaseModel, Field, model_serializer

from .partner import Partner
from .product import Product


class SaleOrderLine(BaseModel):
    product: Product
    quantity: int
    price: float


class SaleOrder(BaseModel):
    partner_id: Partner = Field(..., alias="customer")
    sale_order_lines: list[SaleOrderLine]
