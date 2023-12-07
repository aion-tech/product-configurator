from typing import Annotated

from fastapi import Depends
from odoo.addons.fastapi.dependencies import odoo_env
from odoo.api import Environment

from ..schemas import Partner, Product, SaleOrder, SaleOrderLine


def sale_order_created(
    env: Annotated[Environment, Depends(odoo_env)],
    payload: SaleOrder,
) -> int:
    sale_order_id = env["sale.order"].create(payload.dict())

    return sale_order_id.id
