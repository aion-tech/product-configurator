# -*- coding: utf-8 -*-
import logging
import pytz
import threading
from collections import OrderedDict, defaultdict
from datetime import date, datetime, timedelta
from psycopg2 import sql

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.addons.iap.tools import iap_tools
from odoo.addons.mail.tools import mail_validation
from odoo.addons.phone_validation.tools import phone_validation
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.translate import _
from odoo.tools import date_utils, email_split, is_html_empty, groupby
from odoo.tools.misc import get_lang

_logger = logging.getLogger(__name__)

CRM_LEAD = 'crm.lead'


class CrmLead(models.Model):
    _inherit = CRM_LEAD
    _description = CRM_LEAD

    # Task PES-25
    @api.onchange('partner_id')
    def _compute_company_classification(self):
        for lead in self:
            lead.company_classification = lead.partner_id.company_classification.id

    # Task PES-27
    company_classification = fields.Many2one(string="Company classification",
                                             comodel_name="company.classification",
                                             store=True,
                                             readonly=False)

    # Task PES-25
    @api.depends('partner_id')
    @api.onchange('partner_id')
    def _compute_marketing_consensus(self):
        for lead in self:
            lead.marketing_consensus = lead.partner_id.marketing_consensus

    # Task PES-25
    marketing_consensus = fields.Boolean(string="Marketing consensus",
                                         readonly=False,
                                         default=lambda self: self.partner_id.marketing_consensus if self.partner_id else False,
                                         store=True)

    # Task PES-25
    registration_date = fields.Date(string="Registration Date",
                                    readonly=True,
                                    store=True)

    # Task PES-25
    @api.model
    def create(self, vals):
        _logger.info(str(vals))
        res = super(CrmLead, self).create(vals)
        if not res.registration_date:
            res.registration_date = datetime.now()
        return res