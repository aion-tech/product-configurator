from functools import partial
from unittest import mock

from odoo.addons.fastapi import dependencies
from odoo.addons.fastapi.tests.common import FastAPITransactionCase
from odoo.tests.common import tagged
from odoo.tools import mute_logger
from requests import Response

from ..routers.pescini import pescini_api_router


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

    def _get_token(cls, key: str) -> Response:
        """Get token authenticating with an api key"""
        with cls._create_test_client(
            router=pescini_api_router,
            user=cls.pescini_api_user,
        ) as test_client:
            test_client.headers.update({"API-KEY": key})
            response: Response = test_client.post("/token")
        return response

    def _check_token(cls, api_key: str, token: str) -> Response:
        with cls._create_test_client(
            router=pescini_api_router,
            user=cls.pescini_api_user,
        ) as test_client:
            test_client.headers.update({"API-KEY": api_key})
            response: Response = test_client.post(
                "/check_token",
                json={"token": token},
            )
        return response

    def _post(cls, token: str, endpoint: str, payload: dict) -> Response:
        with cls._create_test_client(
            router=pescini_api_router,
            user=cls.pescini_api_user,
        ) as test_client:
            test_client.headers.update({"Authorization": f"Bearer {token}"})
            response: Response = test_client.post(
                endpoint,
                json=payload,
            )
            return response

    def _get(cls, token: str, endpoint: str) -> Response:
        with cls._create_test_client(
            router=pescini_api_router,
            user=cls.pescini_api_user,
        ) as test_client:
            test_client.headers.update({"Authorization": f"Bearer {token}"})
            response: Response = test_client.get(
                endpoint,
            )
            return response
