from odoo import api, fields, models


class UtmCampaign(models.Model):
    _inherit = "utm.campaign"

    _sql_constraints = [
        ("title_uniq", "unique (title)", "Campaign title already exists !"),
    ]
