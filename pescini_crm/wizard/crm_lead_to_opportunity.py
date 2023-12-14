# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'
    _description = 'Convert Lead to Opportunity (not in mass)'

    def _convert_and_allocate(self, leads, user_ids, team_id=False):
        res = super()._convert_and_allocate(leads, user_ids, team_id=False)
        for lead in leads:
            lead.show_prop = True
        return res
