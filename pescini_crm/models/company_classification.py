# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

COMPANY_CLASSIFICATION = 'company.classification'


class ResPartnerCompayClassification(models.Model):
    _name = COMPANY_CLASSIFICATION
    _description = COMPANY_CLASSIFICATION

    # Task PES-27
    name = fields.Char(string="Name",
                       help="Name",
                       readonly=False,
                       store=True)

    # Task PES-27
    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'),
                                               ('company', 'Company'),
                                               ('pa', 'Public administration')],
                                    readonly=False,
                                    store=True)