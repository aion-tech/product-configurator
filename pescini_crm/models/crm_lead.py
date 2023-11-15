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
    def _compute_marketing_consensus(self):
        for lead in self:
            lead.marketing_consensus = lead.partner_id.marketing_consensus

    # Task PES-25
    marketing_consensus = fields.Boolean(string="Marketing consensus",
                                         readonly=False,
                                         compute='_compute_marketing_consensus',
                                         store=True)

    # Task PES-25
    registration_date = fields.Date(string="Registration Date",
                                    readonly=True,
                                    store=True)

    # Task PES-25
    def create(self, vals):
        res = super(CrmLead, self).create(vals)
        if not res.registration_date:
            res.registration_date = datetime.now()
        return res
    
    def _handle_partner_assignment(self, force_partner_id=False, create_missing=True):
        """ Update customer (partner_id) of leads. Purpose is to set the same
        partner on most leads; either through a newly created partner either
        through a given partner_id.

        :param int force_partner_id: if set, update all leads to that customer;
        :param create_missing: for leads without customer, create a new one
          based on lead information;
        """
        for lead in self:
            if force_partner_id:
                force_partner = self.env['res.partner'].sudo().browse(force_partner_id)                 
                if force_partner and force_partner.parent_id:
                    res = self._prepare_customer_values(self.contact_name, is_company=False, parent_id=force_partner.parent_id.id if force_partner else False)
                else:
                    res = self._prepare_customer_values(self.partner_name, is_company=True)
                lead.partner_id = force_partner_id
                lead.partner_id.write(res) if res else False
            if not lead.partner_id and create_missing:
                partner = lead._create_customer()
                lead.partner_id = partner.id

    # Task PES-27
    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        """ Extract data from lead to create a partner.

        :param name : furtur name of the partner
        :param is_company : True if the partner is a company
        :param parent_id : id of the parent partner (False if no parent)

        :return: dictionary of values to give at res_partner.create()
        """
        email_parts = tools.email_split(self.email_from)
        company_classification = self.company_classification.id if self.company_classification else None
        marketing_consensus = self.marketing_consensus if self.marketing_consensus else False
        if self.contact_name:
            marketing_consensus = False
            company_classification = False
            if self.contact_name != partner_name:
                company_classification = self.company_classification.id if self.company_classification else None,
            else:
                marketing_consensus = self.marketing_consensus

        res = {
            'name': partner_name if partner_name else self.name,
            'user_id': self.env.context.get('default_user_id') or self.user_id.id,
            'comment': self.description,
            'team_id': self.team_id.id,
            'parent_id': parent_id,
            'phone': self.phone,
            'mobile': self.mobile,
            'email': email_parts[0] if email_parts else False,
            'title': self.title.id,
            'function': self.function,
            'street': self.street,
            'street2': self.street2,
            'zip': self.zip,
            'city': self.city,
            'country_id': self.country_id.id,
            'state_id': self.state_id.id,
            'website': self.website,
            'is_company': is_company,
            'type': 'contact',
            'company_classification': company_classification,
            'marketing_consensus': marketing_consensus
        }
        if self.lang_id:
            res['lang'] = self.lang_id.code
        return res

    # Task PES-27
    def create_contact_action(self):
        if not self.partner_id:            
            return self.env["ir.actions.actions"]._for_xml_id("pescini_crm.crm_create_partner_action")