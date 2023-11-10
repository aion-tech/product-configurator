# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime

CRM_LEAD = 'crm.lead'


class CrmLead(models.Model):
    _inherit = CRM_LEAD
    _description = CRM_LEAD

    # Task PES-25
    @api.depends('partner_id')
    def _compute_company_type(self):
        for lead in self:
            lead.company_type = lead.partner_id.company_type

    # Task PES-25
    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'),
                                               ('company', 'Company')],
                                    readonly=False,
                                    compute='_compute_company_type',
                                    store=True)

    # Task PES-25
    @api.depends('partner_id')
    def _compute_marketing_consensus(self):
        for lead in self:
            lead.marketing_consensus = lead.partner_id.marketing_consensus

    # Task PES-25
    marketing_consensus = fields.Boolean(string="Marketing consensus",
                                         readonly=False,
                                         compute='_compute_marketing_consensus',
                                         store=True)

    # Task PES-25
    registration_date = fields.Date(string="Registration Date",
                                    readonly=True,
                                    store=True)

    # Task PES-25
    def create(self, vals):
        res = super(CrmLead, self).create(vals)
        if not res.registration_date:
            res.registration_date = datetime.now()
        return res
        
