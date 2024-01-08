# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

PRODUCT_TEMPLATE = 'product.template'

class PesciniProductTemplate(models.Model):
    _inherit = PRODUCT_TEMPLATE
    _description = PRODUCT_TEMPLATE

    #Task PES-74
    conai_id = fields.Many2one(comodel_name = 'sale.conai',
                               string="Conai",
                               store=True)