from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Tuple, Union

from fastapi import Depends, HTTPException, status
from odoo.addons.fastapi.dependencies import odoo_env
from odoo.addons.pydantic_base_model_odoo import BaseModelOdoo
from odoo.api import Environment
from odoo.osv.expression import AND
from pydantic import BaseModel, Field, computed_field, model_serializer, validator


class State(BaseModelOdoo):
    _omodel: str = "res.country.state"
    name: str
    code: str

    @property
    def _odomain(self) -> List[str | Tuple[str, str, Any]]:
        return [("code", "=", self.code), ("name", "=", self.name)]


class Country(BaseModelOdoo):
    _omodel: str = "res.country"
    code: str

    @property
    def _odomain(self) -> List[str | Tuple[str, str, Any]]:
        return [("code", "=", self.code)]

    @property
    def _opolicy(self):
        return "get"


class CompanyClassificationType(str, Enum):
    person = "individual"
    company = "company"
    pa = "public administration"


class CompanyClassification(BaseModelOdoo):
    """
    Tipologia di partner.
    """

    _omodel: str = "company.classification"

    name: str = Field(..., alias="type_name")
    company_type: CompanyClassificationType

    @property
    def _odomain(self) -> List[str | Tuple[str, str, Any]]:
        return [("name", "=", self.name)]


class Contact(BaseModelOdoo):
    """
    Un contatto collegato ad un Partner.
    Utilizzato per organizzare i dettagli di
    contatto dei dipendenti di un'azienda
    specifica (ad es. CEO, CFO...).
    """

    _omodel: str = "res.partner"
    type: Literal["contact"]
    name: str
    function: Optional[str] = Field(default=None, alias="role_type")
    email: str
    phone: str

    @property
    def _odomain(self) -> List[str | Tuple[str, str, Any]]:
        return [
            "|",
            ("email", "=", self.email),
            ("phone", "=", self.phone),
        ]


class ContactAddress(BaseModelOdoo):
    _omodel: str = "res.partner"
    type: Literal["delivery", "invoice"]
    name: str
    email: str
    phone: str
    street: str
    zip: str
    city: str
    state_id: State = Field(..., alias="state")
    country_id: Country = Field(..., alias="country")

    @property
    def _odomain(self) -> List[str | Tuple[str, str, Any]]:
        return [
            "|",
            ("email", "=", self.email),
            ("phone", "=", self.phone),
        ]


class DeliveryAddress(ContactAddress):
    """
    Un indirizzo di consegna associato ad un Partner.
    """

    type: Literal["delivery"]


class InvoiceAddress(ContactAddress):
    """
    Un indirizzo di fatturazione associato ad un Partner.
    """

    type: Literal["invoice"]


class Partner(BaseModelOdoo):
    """
    Una persona o un'azienda (cliente, fornitore, opportunità, ...)
    """

    _omodel: str = "res.partner"

    name: str = Field(
        ...,
        description=(
            "La ragione sociale dell’azienda o il nome e cognome del privato."
        ),
    )
    company_classification: CompanyClassification = Field(
        ...,
        description="Riportare la tipologia specifica di azienda o di privato cittadino.",
        alias="partner_type",
    )
    email: Optional[str] = None
    phone: Optional[str] = None
    function: Optional[str] = Field(default=None, alias="role_type")
    vat: Optional[str] = Field(default=None, description="Partita IVA")
    street: str = Field(..., description="Via/piazza e numero civico.")
    zip: str
    city: str
    state_id: State = Field(..., description="Provincia", alias="state")
    country_id: Country = Field(..., alias="country")
    marketing_consensus: bool = Field(default=False)
    child_ids: Optional[List[Contact | DeliveryAddress | InvoiceAddress]] = Field(
        default=None,
        alias="contacts",
        description="""Contatti e indirizzi associati al partner. """,
    )

    @computed_field()
    @property
    def is_company(self) -> bool:
        return (
            self.company_classification.company_type != CompanyClassificationType.person
        )

    @computed_field()
    @property
    def company_type(self) -> str:
        return (
            "person"
            if self.company_classification.company_type
            == CompanyClassificationType.person
            else "company"
        )

    @property
    def _opolicy(
        self,
    ) -> Literal["create", "update", "upsert", "skip", "upsert_empty", "update_empty"]:
        partner_id = self._oenv["res.partner"].search(self._odomain)
        # if partner exists and is a company, update empty fields
        # if partner exists and is not a company, update all fields
        # if partner does not exist, skip
        if partner_id:
            is_company = partner_id.is_company and not partner_id.parent_id
            if is_company:
                return "update_empty"
            else:
                return "update"
        # create/update normally otherwise
        return "skip"

    @property
    def _odomain(self) -> List[str | Tuple[str, str, Any]]:
        return ["|", ("email", "=", self.email), ("phone", "=", self.phone)]

    def _o_model_dump_postserialize_hook(self, rec: int, env: Environment) -> int:
        rec = super()._o_model_dump_postserialize_hook(rec, env)
        # Always update marketing_consensus regardless of _opolicy
        partner_id = env["res.partner"].browse(rec)
        partner_id.marketing_consensus = self.marketing_consensus
        return rec

    def _o_model_dump_postprocess_hook(self, vals: Dict[str, Any]) -> Dict[str, Any]:
        vals = super()._o_model_dump_postprocess_hook(vals)
        # raise if partner is linked to an active odoo user.
        # We don't want external parties to be able to change
        # users data and it doesn't make sense to call the api
        # using a user's data.
        existing_partner = self._oenv["res.partner"].search(self._odomain)
        existing_user = existing_partner and self._oenv["res.users"].search(
            [("partner_id", "=", existing_partner.id)]
        )
        if existing_user and existing_user.active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update a user's partner data",
            )
        return vals
