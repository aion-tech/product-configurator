from typing import Annotated, Any, Dict, List

from fastapi import Depends
from odoo.addons.fastapi.dependencies import odoo_env
from odoo.api import Environment
from pydantic import BaseModel

from ..schemas import CrmLead, Partner


def crm_lead_created(
    env: Annotated[Environment, Depends(odoo_env)],
    payload: CrmLead,
) -> int:
    """
    Create a crm.lead record, return its id
    """
    lead_id: int = payload.o_model_dump(env)
    return lead_id
