import datetime
from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Tuple

from fastapi import Depends
from odoo.addons.fastapi.dependencies import odoo_env
from odoo.addons.pydantic_base_model_odoo import BaseModelOdoo
from odoo.api import Environment
from pydantic import BaseModel, Field, model_serializer

from . import Partner


class SourceEnum(str, Enum):
    wordpress = "Wordpress"
    facebook = "Facebook"
    facebook_lead_ads = "Facebook Lead Ads"
    google = "Google"
    linkedin = "Linkedin"


class Source(BaseModelOdoo):
    _omodel: str = "utm.source"

    name: SourceEnum = Field(..., alias="value")

    @property
    def _odomain(self) -> List[str | Tuple[str, str, Any]]:
        return [("name", "=", self.name.value)]

    @property
    def _opolicy(
        self,
    ) -> Literal["create", "update", "upsert", "skip", "upsert_empty", "update_empty"]:
        # new utm sources should be created in they don't exist.
        # skip updating existing ones unless they have empty fields.
        return "upsert_empty"


class Campaign(BaseModelOdoo):
    _omodel: str = "utm.campaign"

    title: str

    @property
    def _odomain(self) -> List[str | Tuple[str, str, Any]]:
        return [("title", "=", self.title)]

    @property
    def _opolicy(
        self,
    ) -> Literal["create", "update", "upsert", "skip", "upsert_empty", "update_empty"]:
        # new utm campaigns should be created in they don't exist.
        # skip updating existing ones unless they have empty fields.
        return "upsert_empty"


class CrmLead(BaseModelOdoo):
    _omodel: str = "crm.lead"
    date_open: datetime.date = Field(..., alias="registration_date")
    name: str = Field(..., alias="title")
    description: str = Field(..., alias="notes")
    source_id: Source = Field(..., alias="source")
    campaign_id: Campaign = Field(..., alias="campaign")
    partner_id: Partner = Field(..., alias="partner")
    partner_name: Optional[str] = Field(
        default=None,
        description=("Ragione sociale dell'azienda"),
        alias="company_name",
    )

    @property
    def _opolicy(
        self,
    ) -> Literal["create", "update", "upsert", "skip", "upsert_empty", "update_empty"]:
        return "create"

    def _o_model_dump_preprocess_hook(self) -> Dict[str, Any]:
        vals: Dict[str, Any] = super()._o_model_dump_preprocess_hook()
        # if no partner_id is found, self.partner_id._opolicy will be set to "skip".
        # In this case the partner vals should be written onto the crm.lead record.
        # It'll be up to odoo users to decide whether to create new opportunities from the crm.lead.
        partner_id = self._oenv["res.partner"].search(self.partner_id._odomain)
        if not partner_id:
            vals = self.partner_id.model_dump()
            # adapt field names to crm.lead field names
            vals["email_from"] = vals.pop("email")
            vals.pop("country_id")
            vals["country_id"] = self.partner_id.country_id.o_model_dump(self._oenv)
            vals.pop("state_id")
            vals["state_id"] = self.partner_id.state_id.o_model_dump(self._oenv)
            vals.pop("company_classification")
            vals[
                "company_classification"
            ] = self.partner_id.company_classification.o_model_dump(self._oenv)
            vals["contact_name"] = self.partner_id.name
            vals[
                "type"
            ] = "lead"  # TODO dynamic based on partner_id existing/not existing?
            vals["function"] = self.partner_id.function

            # remove fields not needed in crm.lead
            vals.pop("vat")
            vals.pop("child_ids")
            # remove computed fields
            vals.pop("is_company")
            vals.pop("company_type")
        return vals
