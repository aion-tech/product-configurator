# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

RES_PARTNER = 'res.partner'

class PesciniResPartner(models.Model):
    _inherit = RES_PARTNER
    _description = RES_PARTNER

    #Task PES-33 
    property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
        string="Account Receivable",
        domain="[('account_type', '=', 'asset_receivable'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
        help="This account will be used instead of the default one as the receivable account for the current partner",
        required=False)
    
    #Task PES-33 
    property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
        string="Account Payable",
        domain="[('account_type', '=', 'liability_payable'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
        help="This account will be used instead of the default one as the payable account for the current partner",
        required=False)
    
    #Task PES-33 
    @api.depends('agent')
    @api.onchange('agent') 
    def _compute_company_id(self):
        for record in self:
            if record.agent:
                record.company_id = self.env.company.id