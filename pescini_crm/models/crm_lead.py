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
    @api.model
    def create(self, vals):
        _logger.info(str(vals))
        res = super(CrmLead, self).create(vals)
        if not res.registration_date:
            res.registration_date = datetime.now()
        return res

    # #Task PES-26
    # def _handle_partner_assignment(self, force_partner_id=False, create_missing=True):
    #     """ Update customer (partner_id) of leads. Purpose is to set the same
    #     partner on most leads; either through a newly created partner either
    #     through a given partner_id.

    #     :param int force_partner_id: if set, update all leads to that customer;
    #     :param create_missing: for leads without customer, create a new one
    #       based on lead information;
    #     """                
    #     for lead in self:
    #         contact_id = False
    #         if force_partner_id:
    #             force_partner = self.env['res.partner'].sudo().browse(
    #                 force_partner_id)
    #             if force_partner and force_partner.parent_id:
    #                 # res = self._prepare_customer_values_with_parent(force_partner)
    #                 res = self._prepare_customer_values(
    #                     self.contact_name, is_company=False, parent_id=force_partner.parent_id.id if force_partner else False)
    #             else:
    #                 # res, contact_id = self._prepare_customer_values_no_parent(force_partner)
    #                 res = self._prepare_customer_values(
    #                     self.partner_name, is_company=True)
    #             lead.partner_id = contact_id.id if contact_id else force_partner_id
    #             lead.partner_id.write(res) if res else False
    #         if not lead.partner_id and create_missing:
    #             partner = lead._create_customer()
    #             lead.partner_id = partner.id

    # #Task PES-27
    # def _create_customer(self):
    #     """ Create a partner from lead data and link it to the lead.

    #     :return: newly-created partner browse record
    #     """
    #     Partner = self.env['res.partner']
    #     contact_name = self.contact_name
    #     company_name = self.partner_name
    #     if not contact_name:
    #         contact_name = Partner._parse_partner_name(
    #             self.email_from)[0] if self.email_from else False

    #     # Task PES-27
    #     if not self.partner_id:
    #         company_vals = {'name': self.partner_name or self.name,
    #                         'company_type': 'company',
    #                         'company_classification': self.company_classification.id if self.company_classification else False,
    #                         'street': self.street,
    #                         'street2': self.street2,
    #                         'city': self.city,
    #                         'state_id': self.state_id.id if self.state_id else False,
    #                         'country_id': self.country_id.id if self.country_id else False,
    #                         'zip': self.zip,
    #                         'website': self.website,
    #                         'lang': self.lang_id.code if self.lang_id else False,
    #                         'team_id': self.team_id.id if self.team_id else False,
    #                         'user_id': self.env.context.get('default_user_id') or self.user_id.id}

    #         contact_vals = {'name': self.contact_name,
    #                         'company_type': 'person',
    #                         'email': self.email_from,
    #                         'function': self.function,
    #                         'phone': self.phone,
    #                         'lang': self.lang_id.code if self.lang_id else False,
    #                         'mobile': self.mobile,
    #                         'user_id': self.env.context.get('default_user_id') or self.user_id.id}
    #         if company_name and contact_name:
    #             company = Partner.sudo().create(company_vals)
    #             contact_vals['parent_id'] = company.id
    #             contact_vals['marketing_consensus'] = self.marketing_consensus
    #             contact = Partner.sudo().create(contact_vals)
    #             return contact
    #         elif company_name and not contact_name:
    #             company_vals['marketing_consensus'] = self.marketing_consensus
    #             company = Partner.sudo().create(company_vals)
    #             return company
    #         elif not company_name and contact_name:
    #             contact_vals['marketing_consensus'] = self.marketing_consensus
    #             contact = Partner.sudo().create(contact_vals)
    #             return contact

    # #Task PES-26
    # def _prepare_customer_values_for_contact(self, partner_id):
    #     if not partner_id:
    #         return
    #     fields_to_check_for_company = [
    #         ('name', self.partner_name),
    #         ('company_classification', self.company_classification.id),
    #         ('street', self.street),
    #         ('street2', self.street2),
    #         ('city', self.city),
    #         ('state_id', self.state_id.id),
    #         ('zip', self.zip),
    #         ('country_id', self.country_id.id),
    #         ('lang', self.lang_id.code),
    #         ('marketing_consensus', self.marketing_consensus),
    #         ('website', self.website),
    #         ('user_id', self.user_id.id),
    #         ('team_id', self.team_id.id),
    #     ]
    #     fields_to_check_for_contact = [
    #         ('name', self.contact_name),
    #         ('title', self.title.id),
    #         ('email', self.email_from),
    #         ('function', self.function),
    #         ('phone', self.phone),
    #         ('mobile', self.mobile),
    #         ('marketing_consensus', self.marketing_consensus),
    #         ('user_id', self.user_id.id),
    #         ('team_id', self.team_id.id),
    #         ('lang', self.lang_id.code)
    #     ]
    #     res = {}
    #     for field, value in fields_to_check_for_contact:
    #         if getattr(partner_id, field) != value:
    #             if value != False:
    #                 res[field] = value
    #     if self.partner_name:
    #         # Create a company and link it to the person as the parent
    #         company_vals = {}
    #         for field, value in fields_to_check_for_company:
    #             if value != False:
    #                 company_vals[field] = value
    #         company_vals['marketing_consensus'] = False
    #         company = self.env['res.partner'].sudo().create(company_vals)
    #         res['parent_id'] = company.id
    #     return res
    
    # # Task PES-27
    # def _prepare_customer_values_with_parent(self, partner_id):
    #     if not partner_id or not partner_id.parent_id:
    #         return
    #     fields_to_check_for_company = [
    #         ('name', self.partner_name),
    #         ('company_classification', self.company_classification.id),
    #         ('street', self.street),
    #         ('street2', self.street2),
    #         ('city', self.city),
    #         ('state_id', self.state_id.id),
    #         ('zip', self.zip),
    #         ('country_id', self.country_id.id),
    #         ('lang', self.lang_id.code),
    #         ('marketing_consensus', self.marketing_consensus),
    #         ('website', self.website),
    #         ('user_id', self.user_id.id),
    #         ('team_id', self.team_id.id),
    #     ]
    #     fields_to_check_for_contact = [
    #         ('name', self.contact_name),
    #         ('title', self.title.id),
    #         ('email', self.email_from),
    #         ('function', self.function),
    #         ('phone', self.phone),
    #         ('mobile', self.mobile),
    #         ('marketing_consensus', self.marketing_consensus),
    #         ('user_id', self.user_id.id),
    #         ('team_id', self.team_id.id),
    #         ('lang', self.lang_id.code)
    #     ]
    #     fields_to_check_for_company = [item for item in fields_to_check_for_company if item[0] != 'marketing_consensus']
    #     company_vals = self._process_fields(fields_to_check_for_company, partner_id.parent_id)
    #     partner_id.parent_id.sudo().write(company_vals)
    #     contact_vlas = self._process_fields(fields_to_check_for_contact, partner_id)
    #     return contact_vlas
    
    # #Task PES-27
    # def _prepare_customer_values_no_parent(self, partner_id):
    #     if not partner_id:
    #         return
    #     fields_to_check_for_company = [
    #         ('name', self.partner_name),
    #         ('company_classification', self.company_classification.id),
    #         ('street', self.street),
    #         ('state_id', self.state_id.id),
    #         ('zip', self.zip),
    #         ('country_id', self.country_id.id),
    #         ('lang', self.lang_id.code),
    #         ('marketing_consensus', self.marketing_consensus),
    #         ('website', self.website),
    #         ('user_id', self.user_id.id),
    #         ('team_id', self.team_id.id),
    #     ]
    #     fields_to_check_for_contact = [
    #         ('name', self.contact_name),
    #         ('title', self.title.id),
    #         ('email', self.email_from),
    #         ('function', self.function),
    #         ('phone', self.phone),
    #         ('mobile', self.mobile),
    #         ('marketing_consensus', self.marketing_consensus),
    #         ('user_id', self.user_id.id),
    #         ('team_id', self.team_id.id),
    #         ('lang', self.lang_id.code)
    #     ]
    #     res = {}
    #     fields_to_check = False

    #     if partner_id.company_type == 'person':
    #         fields_to_check = fields_to_check_for_contact

    #         res = self._process_fields(fields_to_check, partner_id)
    #         if self.partner_name:
    #             company_vals = [item for item in fields_to_check_for_company if item[0] != 'marketing_consensus']
    #             company_id = self.env['res.partner'].sudo().create(dict(company_vals))
    #             res['parent_id'] = company_id.id if company_id else False

    #     contact_id = False
    #     if partner_id.company_type == 'company':                
    #         fields_to_check = fields_to_check_for_company
    #         res = self._process_fields(fields_to_check, partner_id)
    #         if self.contact_name:
    #             contact_vals = self._process_fields(fields_to_check_for_contact, partner_id)
    #             contact_vals['parent_id'] = partner_id.id
    #             contact_id = self.env['res.partner'].sudo().create(contact_vals)
                
    #     return res, contact_id

    # #Task PES-27 
    # def _process_fields(self,fields_to_check, partner_id):
    #     res = {}
    #     for field, value in fields_to_check:
    #         if getattr(partner_id, field) != value:
    #             if value != False:
    #                 res[field] = value
    #     return res


    # # Task PES-27
    # def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
    #     """Extract data from lead to create a partner.

    #     :param partner_name: future name of the partner
    #     :param is_company: True if the partner is a company
    #     :param parent_id: id of the parent partner (False if no parent)

    #     :return: dictionary of values to give at res_partner.create()
    #     """        
    #     # Check if there is no existing partner_id
    #     if not self.partner_id:
    #         return

    #     # Split email parts using Odoo tools module
    #     email_parts = tools.email_split(self.email_from)

    #     # Determine if the existing partner is a company or a person
    #     is_company = True if self.partner_id.company_type == 'company' and not self.partner_id.parent_id else False
    #     is_person = True if self.partner_id.company_type == 'person' and not self.partner_id.parent_id else False

    #     # Define fields to check for when creating a company or contact
    #     fields_to_check_for_company = [
    #         ('name', self.partner_name),
    #         ('company_classification', self.company_classification.id),
    #         ('street', self.street),
    #         ('street2', self.street2),
    #         ('city', self.city),
    #         ('state_id', self.state_id.id),
    #         ('zip', self.zip),
    #         ('country_id', self.country_id.id),
    #         ('lang', self.lang_id.code),
    #         ('marketing_consensus', self.marketing_consensus),
    #         ('website', self.website),
    #         ('user_id', self.user_id.id),
    #         ('team_id', self.team_id.id),
    #     ]
    #     fields_to_check_for_contact = [
    #         ('name', self.contact_name),
    #         ('title', self.title.id),
    #         ('email', self.email_from),
    #         ('function', self.function),
    #         ('phone', self.phone),
    #         ('mobile', self.mobile),
    #         ('marketing_consensus', self.marketing_consensus),
    #         ('user_id', self.user_id.id),
    #         ('team_id', self.team_id.id),
    #         ('lang', self.lang_id.code)
    #     ]

    #     # Create/update partner based on whether it's a company or a person
    #     if is_company:
    #         # If partner_id is a company and vals is company only
    #         res = {}
    #         for field, value in fields_to_check_for_company:
    #             if getattr(self.partner_id, field) != value:
    #                 res[field] = value
    #         if self.contact_name:                
    #             # Create contact and attach it to the company
    #             contact_vals = {}
    #             for field, value in fields_to_check_for_contact:
    #                 contact_vals[field] = value
    #             contact_vals['parent_id'] = self.partner_id.id
    #             contact_id = self.env['res.partner'].sudo().create(contact_vals)
    #             self.write({'partner_id': contact_id.id})
    #     elif is_person:
    #         res = {}
    #         for field, value in fields_to_check_for_contact:
    #             if getattr(self.partner_id, field) != value:
    #                 res[field] = value
    #         if partner_name:
    #             # Create a company and link it to the person as the parent
    #             company_vals = {}
    #             for field, value in fields_to_check_for_company:
    #                 company_vals[field] = value
    #             company_vals['marketing_consensus'] = False
    #             company = self.env['res.partner'].sudo().create(company_vals)
    #             res['parent_id'] = company.id
    #     else:
    #         # Update the parent company with new values
    #         company_vals = {}
    #         for field, value in fields_to_check_for_company:
    #             company_vals[field] = value
    #         company_vals['marketing_consensus'] = False
    #         res = {}
    #         for field, value in fields_to_check_for_contact:
    #             if getattr(self.partner_id, field) != value:
    #                 res[field] = value
    #         self.partner_id.parent_id.write(company_vals)
    #     return res

    # # Task PES-27
    # def create_contact_action(self):
    #     if not self.partner_id:
    #         return self.env["ir.actions.actions"]._for_xml_id("pescini_crm.crm_create_partner_action")
