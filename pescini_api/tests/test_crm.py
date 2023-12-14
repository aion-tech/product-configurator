from typing import Dict

from fastapi import status
from odoo.addons.fastapi import dependencies
from odoo.addons.fastapi.tests.common import FastAPITransactionCase
from pydantic import BaseModel, Field, computed_field, model_serializer, validator
from requests import Response

from ..routers.pescini import pescini_api_router
from ..schemas.partner import Partner
from .common import PesciniApiTestCommon


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

    def _post_crm(self, vals):
        """
        execute a post request to /crm,
        assert its reponse,
        return the id of the created crm.lead
        """
        token = self._get_token(self.crm_api_key.key).json()["token"]
        res = self._post(
            token,
            "/crm",
            vals,
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
