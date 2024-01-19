from datetime import timedelta
from itertools import groupby
from markupsafe import Markup

from odoo import http
from odoo.http import request
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Command
from odoo.osv import expression
from odoo.tools import float_is_zero, format_amount, format_date, html_keep_url, is_html_empty
from odoo.tools.sql import create_index

from odoo.addons.payment import utils as payment_utils

SALE_ORDER = 'sale.order'


class SaleOrder(models.Model):
    _inherit = SALE_ORDER
    _description = SALE_ORDER

    # Task PES-91
    edited_with_ruledesigner = fields.Boolean(string="Edited with ruledesigner",
                                              default=False,
                                              store=True)

    def action_test(self):
        raise UserError(_('test'))