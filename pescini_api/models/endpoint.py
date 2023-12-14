from odoo import fields, models
from odoo.addons.fastapi import dependencies
from odoo.addons.fastapi.dependencies import authenticated_partner_impl

from odoo.addons.fastapi_company_id_header_dependency.dependencies import company_id_from_header
from ..routers.pescini import pescini_api_router

APP_NAME = "pescini"


# -- App
class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[
            (APP_NAME, "Pescini Endpoint"),
        ],
        ondelete={
            APP_NAME: "cascade",
        },
    )

    def _get_fastapi_routers(self):
        if self.app == APP_NAME:
            return [pescini_api_router]
        return super()._get_fastapi_routers()

    def _get_app(self):
        app = super()._get_app()
        if self.app == APP_NAME:
            app.dependency_overrides[dependencies.company_id] = company_id_from_header
        return app
