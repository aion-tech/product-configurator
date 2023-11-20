# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

RES_PARTNER = 'res.partner'


class ResPartner(models.Model):
    _inherit = RES_PARTNER
    _description = RES_PARTNER

    # Task PES-25
    marketing_consensus = fields.Boolean(string="Marketing consensus",
                                         readonly=False,
                                         store=True)
    
    # Task PES-25
    company_classification = fields.Many2one(string="Company classification",
                                             comodel_name="company.classification",
                                             store=True)
