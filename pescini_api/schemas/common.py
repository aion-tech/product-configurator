import logging
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    get_args,
    get_origin,
    get_type_hints,
)

from odoo import Command
from odoo.api import Environment
from pydantic import BaseModel


class Status(BaseModel):
    """Response status & id of the created/updated odoo record"""

    status: str = "ok"
    id: Optional[int] = None
