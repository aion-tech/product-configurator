# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class OpportunityCreateContact(models.TransientModel):
    _name = 'crm.create.contact'
    _description = 'Create new or use existing Customer on Opportuity'

    @api.model
    def default_get(self, fields):
        result = super(OpportunityCreateContact, self).default_get(fields)

        active_model = self._context.get('active_model')
        if active_model != 'crm.lead':
            raise UserError(_('You can only apply this action from a lead.'))

        lead = False
        if result.get('lead_id'):
            lead = self.env['crm.lead'].browse(result['lead_id'])
        elif 'lead_id' in fields and self._context.get('active_id'):
            lead = self.env['crm.lead'].browse(self._context['active_id'])
        if lead:
            result['lead_id'] = lead.id
            partner_id = result.get('partner_id') or lead._find_matching_partner().id
            if 'action' in fields and not result.get('action'):
                result['action'] = 'exist' if partner_id else 'create'
            if 'partner_id' in fields and not result.get('partner_id'):
                result['partner_id'] = partner_id

        return result

    action = fields.Selection([
        ('create', 'Create a new customer'),
        ('exist', 'Link to an existing customer'),
        ('both', 'Link an existing customer to an existing company')
    ], string='Operazione', required=True)
    lead_id = fields.Many2one('crm.lead', "Associated Lead", required=True)
    partner_id = fields.Many2one('res.partner', 'Customer')

    company_id = fields.Many2one('res.partner', 'Company')

    # Task PES-27 
    def action_apply(self):
        """ Convert lead to opportunity or merge lead and opportunity and open
            the freshly created opportunity view.
        """
        self.ensure_one()        
        if self.action == 'create':
            self.lead_id._handle_partner_assignment(create_missing=True)
        elif self.action == 'exist':
            self.lead_id._handle_partner_assignment(force_partner_id=self.partner_id.id, create_missing=False)
        elif self.action == 'both':
            if self.company_id.company_type != 'company':
                raise UserError(_(f'In the Company field you must insert a company!\n{self.company_id.name} is a person.'))
            if self.partner_id.company_type != 'person':
                raise UserError(_(f'In the Customer field you must insert a company!\n{self.partner_id.name} is a company.'))
            self.lead_id._handle_partner_assignment(force_partner_id=self.partner_id.id, create_missing=False, force_company_id=self.company_id.id)
