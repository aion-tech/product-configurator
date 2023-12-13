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
COMMISSION_ASSIGNMENT = 'commission.assignment'


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

    # Task PES-38
    show_prop = fields.Boolean(string="Show Boolean",
                               store=True)

    # Task PES-38
    @api.onchange('partner_id')
    @api.depends('partner_id')
    def _compute_revenue(self):
        for lead in self:
            lead.revenue = lead.partner_id.revenue

    # Task PES-38
    revenue = fields.Float(string="Total revenue",
                           store=True)

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

    # Task PES-38
    create_equals_to_registration = fields.Boolean(string="Create equals to Registration",
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
            res.registration_date = datetime.today()

        # Task PES-38
        if res.create_date and res.registration_date == res.create_date.date():
            res.create_equals_to_registration = True

        # Task PES-33

        # Check if the 'agent' field is present in the values being used for creation
        agent_partner = self.env['res.partner'].browse(
            vals['agent']) if 'agent' in vals else False

        # If 'agent' is present, update the corresponding res.partner record
        if agent_partner:
            # Update the 'agent' field to True and set the 'company_id' to the current company's ID
            agent_partner.write(
                {'agent': True, 'company_id': self.env.company.id})

        # Task PES-48
        self._assign_agent(res)

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

    # def _handle_partner_assignment(self, force_partner_id=False, create_missing=True):
    #     res = super(CrmLead, self)._handle_partner_assignment(force_partner_id=False, create_missing=True)

    # Task PES-48

    def _assign_agent(self, lead):
        # Retrieve the default assignment with priority for the company
        default_assignment = self.env[COMMISSION_ASSIGNMENT].sudo().search([('company_id', '=', self.env.company.id),
                                                                            ('has_priority', '=', True)])
        if not default_assignment:
            raise UserError(
                _('Select default agent in Commission assignment view.'))

        # Check if both company classification and state are present in the lead
        if lead.company_classification and lead.state_id:
            # Retrieve assignments matching the company and filtering based on company classification and state
            assignments = self.env[COMMISSION_ASSIGNMENT].sudo().search(
                [('company_id', '=', self.env.company.id)])
            assignments = assignments.filtered(
                lambda ass: lead.company_classification.id in ass.company_classification_id.ids and lead.state_id.id in ass.state_id.ids)

            # Call the _assign_agent_1 method to determine and set the lead's agent
            lead.agent = self._assign_agent_1(
                assignments, lead, default_assignment)

        # Check if only company classification is present in the lead
        elif lead.company_classification and not lead.state_id:
            # Retrieve assignments matching the company and filtering based on company classification and no state
            assignments = self.env[COMMISSION_ASSIGNMENT].sudo().search(
                [('company_id', '=', self.env.company.id),
                 ('state_id', '=', False)])
            assignments = assignments.filtered(
                lambda ass: lead.company_classification.id in ass.company_classification_id.ids)

            # Call the _assign_agent_1 method to determine and set the lead's agent
            lead.agent = self._assign_agent_1(
                assignments, lead, default_assignment)

        # Check if only state is present in the lead
        elif not lead.company_classification and lead.state_id:
            # Retrieve assignments matching the company and filtering based on no company classification and state
            assignments = self.env[COMMISSION_ASSIGNMENT].sudo().search(
                [('company_id', '=', self.env.company.id),
                 ('company_classification_id', '=', False)])
            assignments = assignments.filtered(
                lambda ass: lead.state_id.id in ass.state_id.ids)

            # Call the _assign_agent_1 method to determine and set the lead's agent
            lead.agent = self._assign_agent_1(
                assignments, lead, default_assignment)

        # If neither company classification nor state is present, set the lead's agent based on the default assignment
        else:
            lead.agent = default_assignment.agent.id if default_assignment else False

    # Task PES-48

    def _assign_agent_1(self, assignments, lead, default_assignment):
        # Check if there are no existing assignments
        if not assignments:
            # Return the ID of the default agent
            return default_assignment.agent.id

        # If there are multiple assignments, determine the agent with the minimum number of leads
        if len(assignments) > 1:
            # Initialize a dictionary to store the count of leads for each agent
            agent_count = {}

            # Iterate through each assignment to calculate the lead count for each agent
            for assign in assignments:
                # Search for leads assigned to the current assignment's agent
                leads = self.env[CRM_LEAD].sudo().search(
                    [('company_id', '=', assign.company_id.id),
                     ('agent', '=', assign.agent.id)])

                # Store the lead count in the agent_count dictionary
                agent_count[assign.agent.id] = int(len(leads)) or 0

            # Find the agent with the minimum lead count
            min_agent = ''
            for key, value in agent_count.items():
                if value == min(agent_count.values()):
                    min_agent = key

            # Return the ID of the agent with the minimum lead count
            return min_agent

        # If there is only one assignment, return the ID of the agent for that assignment
        else:
            return assignments.agent.id
