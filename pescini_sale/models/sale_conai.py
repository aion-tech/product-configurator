# -*- coding: utf-8 -*-

from odoo import models, fields, api

SALE_CONAI = 'sale.conai'

class PesciniSaleConai(models.Model):
    _name = SALE_CONAI
    _description = SALE_CONAI

    #Task PES-74
    name = fields.Char(string='Name',
                       stoe=True)
    
    #Task PES-74
    value = fields.Char(string='Value',
                        store=True)

