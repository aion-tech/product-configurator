# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'
    _description = 'Convert Lead to Opportunity (not in mass)'
    
    # Task PES-27
    def _convert_and_allocate(self, leads, user_ids, team_id=False):
        self.ensure_one()

        for lead in leads:
            if lead.active and self.action != 'nothing':
                partner_id = self.partner_id.id or lead.partner_id.id
                if lead.contact_name:
                    partner_id = self.env ['res.partner'].sudo().search([('name', '=', lead.contact_name)], limit=1)
                    partner_id = partner_id.id
                self._convert_handle_partner(
                    lead, self.action, partner_id)

            lead.convert_opportunity(lead.partner_id, user_ids=False, team_id=False)

        leads_to_allocate = leads
        if not self.force_assignment:
            leads_to_allocate = leads_to_allocate.filtered(lambda lead: not lead.user_id)

        if user_ids:
            leads_to_allocate._handle_salesmen_assignment(user_ids, team_id=team_id)