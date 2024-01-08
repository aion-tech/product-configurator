# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tools import float_is_zero


class PesciniSaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'
    _description = "Sales Advance Payment Invoice"

    #Task PES-75
    def create_invoices(self):   
        # Create invoices based on sale orders
        invoices = self._create_invoices(self.sale_order_ids)
        
        # Iterate through the created invoices
        for invoice in invoices:
            # Get the invoice lines
            lines = invoice.invoice_line_ids
            
            # Filter lines to find those with products marked as stamps
            line_stamp = lines.filtered(lambda l: l.product_id.is_stamp)
            
            # If there are lines with stamps, set 'has_stamp' field of the invoice to True
            if line_stamp:
                invoice.has_stamp = True   

        # Check if the context contains 'open_invoices' flag
        if self.env.context.get('open_invoices'):
            # If 'open_invoices' flag is present, open the invoices view
            return self.sale_order_ids.action_view_invoice()

        # If 'open_invoices' flag is not present, close the window
        return {'type': 'ir.actions.act_window_close'}
