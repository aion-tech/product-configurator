# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

ACCOUNT_MOVE = 'account.move'

class PesciniAccountMove(models.Model):
    _inherit = ACCOUNT_MOVE
    _description = ACCOUNT_MOVE

    #Task PES-75
    has_stamp = fields.Boolean(string='Has stamp',
                               store=True,
                               default=False)