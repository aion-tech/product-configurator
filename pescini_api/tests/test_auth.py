from fastapi import status
from odoo.addons.fastapi import dependencies
from odoo.addons.fastapi.tests.common import FastAPITransactionCase
from requests import Response

from odoo.addons.fastapi_auth_jwt_api_key.dependencies.auth import _generate_jwt
from ..routers.pescini import pescini_api_router
from .common import PesciniApiTestCommon


class PesciniApiTestAuth(PesciniApiTestCommon):
    def test_get_token_valid_key(self) -> None:
        """Test jwt token generation with a valid key"""
        response = self._get_token(self.sale_api_key.key)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json().get("token"))

    def test_get_token_validator_id_crm(self) -> None:
        """A token generated using a CRM validator key
        should be decodeable only by the CRM validator"""
        response = self._get_token(self.crm_api_key.key)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json().get("token")

        # decoding with the CRM validator should work
        response = self._check_token(self.crm_api_key.key, token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json().get("user_id"),
            self.crm_api_key.user_id.id,
        )
        self.assertTrue(response.json().get("aud"))
        self.assertTrue(response.json().get("iss"))
        self.assertTrue(response.json().get("exp"))

        # decoding with the any other validator should fail
        response = self._check_token(self.sale_api_key.key, token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json().get("detail"), "Invalid token")

    def test_get_token_invalid_key(self) -> None:
        """Test jwt token generation with an invalid key"""
        response = self._get_token("IsolemnlyswearthatIamuptonogood")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_validate_token_valid_token(self) -> None:
        """Test jwt token validity with a valid token"""
        token = self._get_token(self.sale_api_key.key).json().get("token")
        response = self._check_token(self.sale_api_key.key, token)
        jsoned = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(jsoned.get("user_id"), self.sale_api_key.user_id.id)
        self.assertTrue(jsoned.get("aud"))
        self.assertTrue(jsoned.get("iss"))
        self.assertTrue(jsoned.get("exp"))

    def test_validate_token_invalid_token(self) -> None:
        """Test jwt token (in)validity with a tampered token"""
        token = self._get_token(self.sale_api_key.key).json().get("token")
        tampered_token = token + "IsolemnlyswearthatIamuptonogood"
        response = self._check_token(self.sale_api_key.key, tampered_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json().get("detail"), "Invalid token")
        #
        invalid_signature_token = _generate_jwt(
            "IsolemnlyswearthatIamuptonogood",
            self.pescini_api_user.id,
            "HS256",
            "pescini.crm.api",
            "pescini.odoo",
        )
        response = self._check_token(self.sale_api_key.key, invalid_signature_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json().get("detail"), "Invalid token")
