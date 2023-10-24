from odoo import fields, models
from odoo.addons.fastapi.dependencies import authenticated_partner_impl

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
