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

    # Task PES-33
    agent = fields.Many2one(comodel_name="res.partner",
                            string="Agent",
                            domain="[('agent','=',True)]",
                            company_depedent=True)

    # Task PES-25
    @api.onchange('partner_id')
    def _compute_company_classification(self):
        # Iterate through each record in the current set of records
        for lead in self:
            # Retrieve the 'company_classification' ID from the 'partner_id'
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
        # Iterate through each record in the current set of records
        for lead in self:
            # Retrieve the 'marketing_consensus' value from the 'partner_id'
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
        # Log the incoming values for debugging purposes
        _logger.info(str(vals))

        # Call the create method of the parent class (superclass) to create the record
        res = super(CrmLead, self).create(vals)

        # If the 'registration_date' is not set, assign the current datetime
        if not res.registration_date:
            res.registration_date = datetime.now()

        # Task PES-33

        # Check if the 'agent' field is present in the values being used for creation
        agent_partner = self.env['res.partner'].browse(
            vals['agent']) if 'agent' in vals else False

        # If 'agent' is present, update the corresponding res.partner record
        if agent_partner:
            # Update the 'agent' field to True and set the 'company_id' to the current company's ID
            agent_partner.write(
                {'agent': True, 'company_id': self.env.company.id})

        # Return the created record
        return res

    def write(self, vals):
        # Task PES-33
        # Check if the 'agent' field is present in the values being updated
        if 'agent' in vals:
            # If 'agent' is present, retrieve the corresponding res.partner record
            agent_partner = self.env['res.partner'].browse(vals['agent'])

            # Check if the 'agent_partner' record exists
            if agent_partner:
                # Update the 'agent' field to True and set the 'company_id' to the current company's ID
                agent_partner.write(
                    {'agent': True, 'company_id': self.env.company.id})

        # Call the write method of the parent class (superclass) to perform the actual update
        return super(CrmLead, self).write(vals)
