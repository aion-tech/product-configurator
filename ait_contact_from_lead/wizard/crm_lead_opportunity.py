# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'
    _description = 'Convert Lead to Opportunity (not in mass)'

    @api.depends('lead_id')
    def _compute_action(self):
        for convert in self:
            if not convert.lead_id:
                convert.action = 'nothing'
            else:
                partner = convert.lead_id._find_matching_partner()
                if partner:
                    convert.action = 'exist'
                elif convert.lead_id.contact_name:
                    convert.action = 'create'
                else:
                    convert.action = 'nothing'

    action = fields.Selection([
        ('create', 'Create a new customer'),
        ('exist', 'Link to an existing customer'),
        ('both', 'Link an existing customer to an existing company'),
        ('nothing', 'Do not link to a customer')
    ], string='Related Customer', compute='_compute_action', readonly=False, store=True, compute_sudo=False)


    company_id = fields.Many2one(comodel_name='res.partner', 
                                 string='Company')

    def _convert_handle_partner(self, lead, action, partner_id):
        # used to propagate user_id (salesman) on created partners during conversion
        if action == 'both':
            lead.with_context(default_user_id=self.user_id.id)._handle_partner_assignment(
                force_partner_id=partner_id,
                create_missing=False,
                force_company_id=self.company_id.id
            )
        else:
            lead.with_context(default_user_id=self.user_id.id)._handle_partner_assignment(
                force_partner_id=partner_id,
                create_missing=(action == 'create')
            )
    # Task PES-27 
    # def action_apply(self):
    #     """ Convert lead to opportunity or merge lead and opportunity and open
    #         the freshly created opportunity view.
    #     """
    #     self.ensure_one()        
    #     if self.action == 'create':
    #         self.lead_id._handle_partner_assignment(create_missing=True)
    #     elif self.action == 'exist':
    #         self.lead_id._handle_partner_assignment(force_partner_id=self.partner_id.id, create_missing=False)
    #     elif self.action == 'both':
    #         if self.company_id.company_type != 'company':
    #             raise UserError(_(f'In the Company field you must insert a company!\n{self.company_id.name} is a person.'))
    #         if self.partner_id.company_type != 'person':
    #             raise UserError(_(f'In the Customer field you must insert a company!\n{self.partner_id.name} is a company.'))
    #         self.lead_id._handle_partner_assignment(force_partner_id=self.partner_id.id, create_missing=False, force_company_id=self.company_id.id)
