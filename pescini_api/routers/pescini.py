from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from odoo import SUPERUSER_ID, api, models
from odoo.addons.auth_api_key.models.auth_api_key import AuthApiKey
from odoo.addons.auth_jwt.exceptions import UnauthorizedInvalidToken
from odoo.addons.base.models.res_partner import Partner
from odoo.addons.base.models.res_users import Users
from odoo.addons.fastapi.dependencies import odoo_env
from odoo.addons.fastapi_auth_jwt.dependencies import AuthJwtPartner, AuthJwtPayload
from odoo.api import Environment

from odoo.addons.fastapi_auth_jwt_api_key.dependencies.auth import (
    AuthJwtUser,
    api_key_auth_user,
    api_key_record,
    generate_jwt_token,
)
from ..dependencies.crm import crm_lead_created
from ..dependencies.sale import sale_order_created
from ..schemas import CrmLead, Partner, SaleOrder, Status
from odoo.addons.fastapi_auth_jwt_api_key.schemas import DecodedJwtToken, JwtToken

pescini_api_router = APIRouter()


# -- Auth
@pescini_api_router.post("/token", response_model=JwtToken)
def get_token(
    env: Annotated[Environment, Depends(odoo_env)],
    user: Annotated[Users, Depends(api_key_auth_user)],
    jwt_token: Annotated[JwtToken, Depends(generate_jwt_token)],
) -> JwtToken:
    """
    Request an access token
    """
    return jwt_token


@pescini_api_router.post("/check_token", response_model=DecodedJwtToken)
def check_token(
    env: Annotated[
        Environment,
        Depends(odoo_env),
    ],
    api_key_id: Annotated[AuthApiKey, Depends(api_key_record)],
    jwt_token: JwtToken,
) -> DecodedJwtToken:
    """
    Check if an access token is valid
    """
    validator_id = api_key_id.jwt_validator_id
    try:
        return DecodedJwtToken(
            **validator_id._decode(jwt_token.token, secret=validator_id.secret_key)
        )
    except UnauthorizedInvalidToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


# -- Sale
@pescini_api_router.post("/sale", response_model=Status)
def create_sale_order(
    env: Annotated[Environment, Depends(odoo_env)],
    user: Annotated[
        Users,
        Depends(AuthJwtUser(validator_name="jwt_validator_pescini_sale")),
    ],
    sale_order_id: Annotated[
        int,
        Depends(sale_order_created),
    ],
) -> Status:
    """
    Create a sale order
    """
    return Status(id=sale_order_id)


# -- CRM
@pescini_api_router.post("/crm", response_model=Status)
def create_crm_lead(
    env: Annotated[Environment, Depends(odoo_env)],
    user: Annotated[
        Users,
        Depends(AuthJwtUser(validator_name="jwt_validator_pescini_crm")),
    ],
    crm_lead_id: Annotated[
        int,
        Depends(crm_lead_created),
    ],
) -> Status:
    """
    Create an opportunity/lead
    """
    return Status(id=crm_lead_id)
