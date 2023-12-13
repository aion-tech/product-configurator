from enum import Enum, IntEnum
from typing import Any, Dict

from pydantic import BaseModel, model_serializer


class Product(BaseModel):
    name: str
    sku: str
