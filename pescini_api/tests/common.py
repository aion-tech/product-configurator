from functools import partial
from typing import Literal
from unittest import mock

from odoo.addons.fastapi import dependencies
from odoo.addons.fastapi.dependencies import company_id, fastapi_endpoint
from odoo.addons.fastapi.tests.common import FastAPITransactionCase
from odoo.tests.common import tagged
from odoo.tools import mute_logger
from requests import Response

from ..routers.pescini import pescini_api_router

COMPANY_1_VAT = "IT03450700988"  # PESCINI
COMPANY_2_VAT = "IT02944900980"  # ALUVETRO


@tagged("post_install", "fastapi", "pescini")
class PesciniApiTestCommon(FastAPITransactionCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.test_router = pescini_api_router
        cls.pescini_api_user = cls.env.ref("pescini_api.pescini_api_user")
        cls.jwt_validator_crm = cls.env.ref("pescini_api.pescini_validator_crm")
        cls.jwt_validator_sale = cls.env.ref("pescini_api.pescini_validator_sale")
        cls.crm_api_key = cls.env["auth.api.key"].create(
            {
                "name": "Crm Api Key",
                "user_id": cls.pescini_api_user.id,
                "key": "MischiefManaged",
                "jwt_validator_id": cls.jwt_validator_crm.id,
            }
        )
        cls.sale_api_key = cls.env["auth.api.key"].create(
            {
                "name": "Sale Api Key",
                "user_id": cls.pescini_api_user.id,
                "key": "Alohomora",
                "jwt_validator_id": cls.jwt_validator_sale.id,
            }
        )
        # set up multi company
        # c1
        cls.company1 = cls.env.ref("base.main_company")
        cls.company1.partner_id.vat = COMPANY_1_VAT
        # c2
        cls.company2 = cls.env["res.company"].create({"name": "Company2"})
        cls.company2.partner_id.vat = COMPANY_2_VAT
        # multi company user
        cls.pescini_api_user.company_ids = [(6, 0, [cls.company2.id, cls.company1.id])]

    def _create_pescini_test_client(cls):
        pescini_app = cls.env.ref("pescini_api.pescini_endpoint")
        return cls._create_test_client(
            router=pescini_api_router,
            user=cls.pescini_api_user,
            dependency_overrides={
                fastapi_endpoint: partial(lambda a: a, pescini_app),
            },
        )

    def _get_token(cls, key: str) -> Response:
        """Get token authenticating with an api key"""
        with cls._create_pescini_test_client() as test_client:
            test_client.headers.update({"API-KEY": key})
            response: Response = test_client.post("/token")
        return response

    def _check_token(cls, api_key: str, token: str) -> Response:
        with cls._create_pescini_test_client() as test_client:
            test_client.headers.update({"API-KEY": api_key})
            response: Response = test_client.post(
                "/check_token",
                json={"token": token},
            )
        return response

    def _request(
        cls,
        method: Literal["get", "post"],
        token: str,
        endpoint: str,
        payload: dict,
        company: str = COMPANY_1_VAT,
    ):
        with cls._create_pescini_test_client() as test_client:
            test_client.headers.update(
                {
                    "Authorization": f"Bearer {token}",
                    "X-Odoo-Company": company,
                }
            )
            # mock odoo.addons.fastapi_company_id_header_dependency.dependencies.company.company_id_from_header
            test_client.app.dependency_overrides[company_id] = (
                lambda: test_client.headers.get("X-Odoo-Company")
                and cls.env["res.company"]
                .sudo()
                .search([("vat", "=", test_client.headers.get("X-Odoo-Company"))])
                .id
                or None
            )
            response: Response = getattr(test_client, method)(
                endpoint,
                json=payload,
            )
            return response
