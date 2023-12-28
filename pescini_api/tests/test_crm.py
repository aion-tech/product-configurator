from typing import Dict

from fastapi import status
from odoo.addons.fastapi import dependencies
from odoo.addons.fastapi.dependencies import company_id
from odoo.addons.fastapi.tests.common import FastAPITransactionCase
from pydantic import BaseModel, Field, computed_field, model_serializer, validator
from requests import Response

from ..routers.pescini import pescini_api_router
from ..schemas.partner import Partner
from .common import COMPANY_1_VAT, COMPANY_2_VAT, PesciniApiTestCommon


class PesciniApiTestCrm(PesciniApiTestCommon):
    def setUp(self):
        super(PesciniApiTestCrm, self).setUp()

        self.company_vals = {
            "name": "Hogwarts School of Witchcraft and Wizardry",
            "partner_type": {
                "type_name": "School",
                "company_type": "company",
            },
            "email": "hogwarts@school.edu",
            "phone": "1-267-436-5109",
            "street": "Hogwarts Castle, Highlands",
            "zip": "20100",
            "city": "Milano",
            "state": {"name": "Milano", "code": "MI"},
            "country": {"code": "US"},
            "marketing_consensus": True,
        }

        self.company_lead_vals = {
            "registration_date": "2023-11-01",
            "source": {"value": "Wordpress"},
            "campaign": {"title": "Campaign 1"},
            "notes": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            "title": "A Company Crm Lead",
            "partner": self.company_vals,
        }

        self.person_vals = {
            "name": "Hermione Granger",
            "partner_type": {
                "type_name": "Student",
                "company_type": "individual",
            },
            "role_type": "Gryffindor Student",
            "email": "h.granger@hogwarts.edu",
            "phone": "000-4815162342-000",
            "street": "Hogwarts Castle, Highlands, Gryffindor dormitory",
            "zip": "10121",
            "city": "Torino",
            "state": {"name": "Torino", "code": "TO"},
            "country": {"code": "IT"},
            "marketing_consensus": True,
        }

        self.person_lead_vals = {
            "registration_date": "2022-10-02",
            "source": {"value": "Linkedin"},
            "campaign": {"title": "Barbarossa"},
            "notes": "Justo laoreet sit amet cursus sit amet dictum sit.",
            "title": "A Person Crm Lead",
            "partner": self.person_vals,
            "company_name": "Hogwarts School of Witchcraft and Wizardry",
        }

    def _post_crm(self, vals, company: str = COMPANY_1_VAT):
        """
        execute a post request to /crm,
        assert its reponse,
        return the id of the created crm.lead
        """
        token = self._get_token(self.crm_api_key.key).json()["token"]
        res = self._request(
            "post",
            token,
            "/crm",
            vals,
            company=company,
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()["status"], "ok")
        self.assertTrue(res.json()["id"])
        # user is defined in _create_test_client while in tests.
        # In an actual api call it should be the user registered
        # in the api key user_id field.
        self.assertEqual(
            self.env["crm.lead"].browse(res.json()["id"]).create_uid.id,
            self.pescini_api_user.id,
        )
        return res.json()["id"]

    def test_create_lead_existing_company(self):
        """
        Create crm.lead for an existing company
        """
        existing_company_id = self.env["res.partner"].create(
            {
                "name": "Pippo",
                "email": self.company_vals["email"],
                "is_company": True,
            }
        )
        lead = self._post_crm(self.company_lead_vals)
        lead_id = self.env["crm.lead"].browse(lead)
        self.assertTrue(len(lead_id.partner_id) > 0)
        # existing partner should've been linked to newly created crm.lead
        self.assertEqual(
            lead_id.partner_id.id,
            existing_company_id.id,
        )

        # previously populated fields on partner should not have been updated
        self.assertNotEqual(
            lead_id.partner_id.name,
            self.company_vals["name"],
        )
        self.assertEqual(
            lead_id.partner_id.name,
            "Pippo",
        )

        # previously empty fields on partner should've been populated
        self.assertEqual(
            lead_id.partner_id.company_type,
            "company",
        )
        self.assertEqual(
            lead_id.partner_id.email,
            self.company_vals["email"],
        )
        self.assertEqual(
            lead_id.partner_id.phone,
            self.company_vals["phone"],
        )
        self.assertEqual(
            lead_id.partner_id.street,
            self.company_vals["street"],
        )
        self.assertEqual(
            lead_id.partner_id.zip,
            self.company_vals["zip"],
        )
        self.assertEqual(
            lead_id.partner_id.city,
            self.company_vals["city"],
        )
        self.assertEqual(
            lead_id.partner_id.state_id.name,
            self.company_vals["state"]["name"],
        )
        self.assertEqual(
            lead_id.partner_id.state_id.code,
            self.company_vals["state"]["code"],
        )
        self.assertEqual(
            lead_id.partner_id.country_id.code,
            self.company_vals["country"]["code"],
        )
        self.assertEqual(
            lead_id.partner_id.marketing_consensus,
            self.company_vals["marketing_consensus"],
        )
        self.assertEqual(
            lead_id.description.unescape(),
            f"<p>{self.company_lead_vals['notes']}</p>",
        )
        self.assertEqual(
            lead_id.source_id.name,
            self.company_lead_vals["source"]["value"],
        )
        self.assertEqual(
            lead_id.campaign_id.title,
            self.company_lead_vals["campaign"]["title"],
        )
        self.assertEqual(
            lead_id.campaign_id.name,
            self.company_lead_vals["campaign"]["title"],
        )
        self.assertFalse(lead_id.user_id)
        self.assertFalse(lead_id.team_id)

    def test_create_lead_new_company(self):
        lead = self._post_crm(self.company_lead_vals)
        lead_id = self.env["crm.lead"].browse(lead)
        # partner doesn't exist yet.
        # no partner should've been linked to newly created crm.lead
        self.assertFalse(lead_id.partner_id)

        # payload should've been written onto the crm.lead record
        self.assertEqual(
            lead_id.name,
            self.company_lead_vals["title"],
        )
        self.assertEqual(
            lead_id.email_from,
            self.company_lead_vals["partner"]["email"],
        )
        self.assertEqual(
            lead_id.phone,
            self.company_lead_vals["partner"]["phone"],
        )

        self.assertEqual(
            lead_id.street,
            self.company_lead_vals["partner"]["street"],
        )
        self.assertEqual(
            lead_id.zip,
            self.company_lead_vals["partner"]["zip"],
        )
        self.assertEqual(
            lead_id.city,
            self.company_lead_vals["partner"]["city"],
        )
        self.assertEqual(
            lead_id.state_id.name,
            self.company_lead_vals["partner"]["state"]["name"],
        )
        self.assertEqual(
            lead_id.state_id.code,
            self.company_lead_vals["partner"]["state"]["code"],
        )
        self.assertEqual(
            lead_id.country_id.code,
            self.company_lead_vals["partner"]["country"]["code"],
        )
        self.assertEqual(
            lead_id.marketing_consensus,
            self.company_lead_vals["partner"]["marketing_consensus"],
        )
        self.assertEqual(
            lead_id.description.unescape(),
            f"<p>{self.company_lead_vals['notes']}</p>",
        )
        self.assertEqual(
            lead_id.source_id.name,
            self.company_lead_vals["source"]["value"],
        )
        self.assertEqual(
            lead_id.campaign_id.title,
            self.company_lead_vals["campaign"]["title"],
        )
        self.assertEqual(
            lead_id.campaign_id.name,
            self.company_lead_vals["campaign"]["title"],
        )
        self.assertFalse(lead_id.user_id)
        self.assertFalse(lead_id.team_id)

    def test_create_lead_existing_person(self):
        company_id = self.env["res.partner"].create(
            {
                "name": self.company_vals["name"],
                "email": self.company_vals["email"],
                "is_company": True,
            }
        )
        existing_partner_id = self.env["res.partner"].create(
            {
                "name": "Emma Watson",
                "email": self.person_vals["email"],
                "is_company": False,
                "parent_id": company_id.id,
                "function": "Actress",
            }
        )
        lead = self._post_crm(self.person_lead_vals)
        lead_id = self.env["crm.lead"].browse(lead)

        # existing partner should've been linked to newly created crm.lead
        self.assertEqual(
            lead_id.partner_id.id,
            existing_partner_id.id,
        )

        # all partner fields should've been updated (both populated and empty ones)
        self.assertEqual(
            existing_partner_id.name,
            self.person_vals["name"],
        )
        self.assertEqual(
            existing_partner_id.company_classification.name,
            "Student",
        )
        self.assertEqual(
            existing_partner_id.company_classification.company_type,
            "person",
        )
        self.assertEqual(
            existing_partner_id.email,
            self.person_vals["email"],
        )
        self.assertEqual(
            existing_partner_id.phone,
            self.person_vals["phone"],
        )
        self.assertEqual(
            existing_partner_id.function,
            self.person_vals["role_type"],
        )
        self.assertEqual(
            existing_partner_id.street,
            self.person_vals["street"],
        )
        self.assertEqual(
            existing_partner_id.zip,
            self.person_vals["zip"],
        )
        self.assertEqual(
            existing_partner_id.city,
            self.person_vals["city"],
        )
        self.assertEqual(
            existing_partner_id.state_id.name,
            self.person_vals["state"]["name"],
        )
        self.assertEqual(
            existing_partner_id.state_id.code,
            self.person_vals["state"]["code"],
        )
        self.assertEqual(
            existing_partner_id.country_id.code,
            self.person_vals["country"]["code"],
        )
        self.assertEqual(
            existing_partner_id.marketing_consensus,
            self.person_vals["marketing_consensus"],
        )
        self.assertEqual(
            lead_id.description.unescape(),
            f"<p>{self.person_lead_vals['notes']}</p>",
        )
        self.assertEqual(
            lead_id.source_id.name,
            self.person_lead_vals["source"]["value"],
        )
        self.assertEqual(
            lead_id.campaign_id.title,
            self.person_lead_vals["campaign"]["title"],
        )
        self.assertEqual(
            lead_id.campaign_id.name,
            self.person_lead_vals["campaign"]["title"],
        )
        self.assertFalse(lead_id.user_id)
        self.assertFalse(lead_id.team_id)

    def test_create_lead_new_person(self):
        lead = self._post_crm(self.person_lead_vals)
        lead_id = self.env["crm.lead"].browse(lead)
        # partner doesn't exist yet.
        # no partner should've been linked to newly created crm.lead
        self.assertFalse(lead_id.partner_id)

        # payload vals should've been written onto the crm.lead record
        self.assertEqual(
            lead_id.name,
            self.person_lead_vals["title"],
        )
        self.assertEqual(
            lead_id.company_classification.name,
            "Student",
        )
        self.assertEqual(
            lead_id.company_classification.company_type,
            "person",
        )
        self.assertEqual(
            lead_id.partner_name,
            self.person_lead_vals["company_name"],
        )
        self.assertEqual(
            lead_id.contact_name,
            self.person_lead_vals["partner"]["name"],
        )
        self.assertEqual(
            lead_id.email_from,
            self.person_lead_vals["partner"]["email"],
        )
        self.assertEqual(
            lead_id.phone,
            self.person_lead_vals["partner"]["phone"],
        )
        self.assertEqual(
            lead_id.function,
            self.person_lead_vals["partner"]["role_type"],
        )
        self.assertEqual(
            lead_id.street,
            self.person_lead_vals["partner"]["street"],
        )
        self.assertEqual(
            lead_id.zip,
            self.person_lead_vals["partner"]["zip"],
        )
        self.assertEqual(
            lead_id.city,
            self.person_lead_vals["partner"]["city"],
        )
        self.assertEqual(
            lead_id.state_id.name,
            self.person_lead_vals["partner"]["state"]["name"],
        )
        self.assertEqual(
            lead_id.state_id.code,
            self.person_lead_vals["partner"]["state"]["code"],
        )
        self.assertEqual(
            lead_id.country_id.code,
            self.person_lead_vals["partner"]["country"]["code"],
        )
        self.assertEqual(
            lead_id.marketing_consensus,
            self.person_lead_vals["partner"]["marketing_consensus"],
        )
        self.assertEqual(
            lead_id.description.unescape(),
            f"<p>{self.person_lead_vals['notes']}</p>",
        )
        self.assertEqual(
            lead_id.source_id.name,
            self.person_lead_vals["source"]["value"],
        )
        self.assertEqual(
            lead_id.campaign_id.title,
            self.person_lead_vals["campaign"]["title"],
        )
        self.assertEqual(
            lead_id.campaign_id.name,
            self.person_lead_vals["campaign"]["title"],
        )
        self.assertFalse(lead_id.user_id)
        self.assertFalse(lead_id.team_id)

    def test_partner_postserialize_hook(self):
        existing_partner_id = self.env["res.partner"].create(
            {
                "name": "Hogwarts School of Witchcraft and Wizardry",
                "email": self.company_vals["email"],
                "phone": self.company_vals["phone"],
            }
        )
        lead = self._post_crm(self.company_lead_vals)
        lead_id = self.env["crm.lead"].browse(lead)
        self.assertEqual(
            lead_id.partner_id.id,
            existing_partner_id.id,
        )
        self.assertEqual(
            existing_partner_id.marketing_consensus,
            self.company_vals["marketing_consensus"],
        )

        self.company_vals.update({"marketing_consensus": False})
        self._post_crm(self.company_lead_vals)
        # by default existing company vals shouldn't be updated if they're not empty
        # (see Partner._opolicy). marketing_consensus should've been updated anyway
        # (see Parnter._o_model_dump_postserialize_hook)
        self.assertEqual(
            existing_partner_id.marketing_consensus,
            False,
        )

    def test_multi_company_crm_lead(self):
        # company1
        lead = self._post_crm(self.person_lead_vals)
        lead_id = self.env["crm.lead"].browse(lead)
        self.assertEqual(
            lead_id.company_id.id,
            self.company1.id,
        )
        self.assertFalse(lead_id.partner_id)

        # company2
        lead2 = self._post_crm(
            self.person_lead_vals,
            company=COMPANY_2_VAT,
        )
        lead_id2 = self.env["crm.lead"].browse(lead2)
        self.assertEqual(
            lead_id2.company_id.id,
            self.company2.id,
        )
        self.assertFalse(lead_id2.partner_id)

    def test_multi_company_crm_lead_no_company_in_headers(self):
        """
        If no company is specified in the request headers,
        the lead should be created using the default company.
        (see https://github.com/OCA/rest-framework/pull/365/files)
        """
        token = self._get_token(self.crm_api_key.key).json()["token"]
        with self._create_pescini_test_client() as test_client:
            test_client.headers.update(
                {
                    "Authorization": f"Bearer {token}",
                    # No company in headers
                    # "X-Odoo-Company": COMPANY_2_VAT,
                }
            )
            # mock odoo.addons.fastapi_company_id_header_dependency.dependencies.company_id_from_header
            test_client.app.dependency_overrides[company_id] = (
                lambda: test_client.headers.get("X-Odoo-Company")
                and self.env["res.company"]
                .sudo()
                .search([("vat", "=", test_client.headers.get("X-Odoo-Company"))])
                .id
                or None
            )
            response = test_client.post(
                "/crm",
                json=self.person_lead_vals,
            )
            lead_id = self.env["crm.lead"].browse(response.json()["id"])

            self.assertEqual(
                lead_id.company_id.id,
                self.env.ref("pescini_api.pescini_endpoint").user_id.company_id.id,
            )

    def test_update_user_partner(self):
        """
        Trying to update a partner linked to an active user should raise.
        """
        self.env["res.users"].with_context(
            mail_create_nolog=True,
            mail_create_nosubscribe=True,
            mail_notrack=True,
            no_reset_password=True,
            tracking_disable=True,
        ).create(
            {
                "name": "Hermione Granger",
                "login": "h.granger@hogwarts.edu",
                "email": "h.granger@hogwarts.edu",
            }
        )
        token = self._get_token(self.crm_api_key.key).json()["token"]
        res = self._request(
            "post",
            token,
            "/crm",
            self.person_lead_vals,
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            res.json()["detail"],
            "Cannot update a user's partner data",
        )

    def test_lead_creation_with_child_ids(self):
        # if no res.partner is found, vals should be written onto the crm.lead record.
        # Empty partner fields should be populated with data from the first contact.
        contact_vals = {
            "name": "Ron Weasley",
            "email": "r.weasley@hogwarts.edu",
            "role_type": "Gryffindor Student",
            "type": "contact",
        }

        self.company_lead_vals["partner"].update(
            dict(
                name="",
                email="",
                contacts=[contact_vals],
            )
        )
        lead = self._post_crm(self.company_lead_vals)
        lead_id = self.env["crm.lead"].browse(lead)
        # partner doesn't exist yet.
        # no partner should've been linked to newly created crm.lead
        self.assertFalse(lead_id.partner_id)

        self.assertEqual(
            lead_id.contact_name,
            contact_vals["name"],
        )
        self.assertEqual(
            lead_id.email_from,
            contact_vals["email"],
        )
        self.assertEqual(
            lead_id.function,
            contact_vals["role_type"],
        )
