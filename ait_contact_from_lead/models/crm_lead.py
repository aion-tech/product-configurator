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
RES_PARTNER = 'res.partner'


class CrmLead(models.Model):
    _inherit = CRM_LEAD
    _description = CRM_LEAD

    # Task PES-27
    def _handle_partner_assignment(self, force_partner_id=False, create_missing=True, force_company_id=False):
        """ Update customer (partner_id) of leads. Purpose is to set the same
        partner on most leads; either through a newly created partner either
        through a given partner_id.

        :param int force_partner_id: if set, update all leads to that customer;
        :param create_missing: for leads without customer, create a new one
          based on lead information;
        """
        for lead in self:
            contact_id = False  
            res = {}          
            if force_company_id and force_partner_id:                
                force_partner = self.env[RES_PARTNER].sudo().browse(
                    force_partner_id)
                force_company_id = self.env[RES_PARTNER].sudo().browse(
                    force_company_id)
                res = self._prepare_both_existing(force_partner, force_company_id)                
            elif force_partner_id and not force_company_id:
                force_partner = self.env[RES_PARTNER].sudo().browse(
                    force_partner_id)
                if force_partner and force_partner.parent_id:
                    res = self._prepare_customer_values_with_parent(
                        force_partner)
                else:
                    res, contact_id = self._prepare_customer_values_no_parent(
                        force_partner)
            lead.partner_id = contact_id.id if contact_id else force_partner_id
            if 'lang_id' in res.keys():
                lang = res['lang_id']
                del res['lang_id']
                res['lang'] = lang
            lead.partner_id.write(res) if res else False
            if not lead.partner_id and create_missing:
                partner = lead._create_customer()
                lead.partner_id = partner.id

    # Task PES-27
    def _check_fields(self, vals, partner, dict):
        for field, value in vals:
            if getattr(partner, field) != value:
                if value != False:
                    dict[field] = value
        return dict
    #Task PES-27
    def _prepare_both_existing(self, force_partner_id, force_company_id):
        contact_vals = self._fields_to_check_for_contact_crm()
        contact_res = {}
        company_res = {}
        company_vals = self._fields_to_check_for_company()

        contact_res = self._check_fields(contact_vals, self, contact_res)
        contact_res['parent_id'] = force_company_id.id
        force_partner_id.parent_id = force_company_id.id

        company_res = self._check_fields(company_vals, force_company_id, company_res)

        keys = []
        for key, value in company_res.items():
            if force_company_id.mapped(key) and force_company_id.mapped(key)[0]:
                keys.append(key)
        if keys:
            for key in keys:
                del company_res[key]
        force_company_id.write(company_res)
        
        return contact_res

    # Task PES-27
    def _create_customer(self):
        """ Create a partner from lead data and link it to the lead.

        :return: newly-created partner browse record
        """
        Partner = self.env[RES_PARTNER]
        contact_name = self.contact_name
        company_name = self.partner_name
        if not contact_name:
            contact_name = Partner._parse_partner_name(
                self.email_from)[0] if self.email_from else False

        # Task PES-27
        if not self.partner_id:
            default_user_id = self.env.context.get('default_user_id')
            company_vals = {'name': self.partner_name or self.name,
                            'company_type': 'company',
                            # 'company_classification': self.company_classification.id if self.company_classification else False,
                            'street': self.street,
                            'street2': self.street2,
                            'city': self.city,
                            'state_id': self.state_id.id if self.state_id else False,
                            'country_id': self.country_id.id if self.country_id else False,
                            'zip': self.zip,
                            'website': self.website,
                            'lang': self.lang_id.code if self.lang_id else False,
                            'team_id': self.team_id.id if self.team_id else False,
                            'user_id': default_user_id or self.user_id.id}

            contact_vals = {'name': self.contact_name,
                            'company_type': 'person',
                            'email': self.email_from,
                            'function': self.function,
                            'phone': self.phone,
                            'lang': self.lang_id.code if self.lang_id else False,
                            'mobile': self.mobile,
                            'user_id': default_user_id or self.user_id.id}
            if company_name and contact_name:
                company = Partner.sudo().create(company_vals)
                if company.phone:
                    company.phone = False
                if company.mobile:
                    company.mobile = False
                contact_vals['parent_id'] = company.id
                # contact_vals['marketing_consensus'] = self.marketing_consensus
                contact = Partner.sudo().create(contact_vals)
                return contact
            elif company_name and not contact_name:
                # company_vals['marketing_consensus'] = self.marketing_consensus
                company = Partner.sudo().create(company_vals)
                if company.phone:
                    company.phone = False
                if company.mobile:
                    company.mobile = False
                return company
            elif not company_name and contact_name:
                # contact_vals['marketing_consensus'] = self.marketing_consensus
                contact = Partner.sudo().create(contact_vals)
                return contact

    def _fields_to_check_for_company(self):
        fields_to_check_for_company = [
            ('name', self.partner_name),
            # ('company_classification', self.company_classification.id),
            ('street', self.street),
            ('street2', self.street2),
            ('city', self.city),
            ('state_id', self.state_id.id),
            ('zip', self.zip),
            ('country_id', self.country_id.id),
            ('lang', self.lang_id.code),
            # ('marketing_consensus', self.marketing_consensus),
            ('website', self.website),
            ('user_id', self.user_id.id),
            ('team_id', self.team_id.id),
        ]
        return fields_to_check_for_company
    
    def _fields_to_check_for_contact_crm(self):
        fields_to_check_for_contact = [
            ('contact_name', self.contact_name),
            ('title', self.title.id),
            ('email_from', self.email_from),
            ('function', self.function),
            ('phone', self.phone),
            ('mobile', self.mobile),
            # ('marketing_consensus', self.marketing_consensus),
            ('user_id', self.user_id.id),
            ('team_id', self.team_id.id),
            ('lang_id', self.lang_id.code)
        ]
        return fields_to_check_for_contact
    def _fields_to_check_for_contact(self):
        fields_to_check_for_contact = [
            ('name', self.contact_name),
            ('title', self.title.id),
            ('email', self.email_from),
            ('function', self.function),
            ('phone', self.phone),
            ('mobile', self.mobile),
            # ('marketing_consensus', self.marketing_consensus),
            ('user_id', self.user_id.id),
            ('team_id', self.team_id.id),
            ('lang', self.lang_id.code)
        ]
        return fields_to_check_for_contact
    # Task PES-27
    def _prepare_customer_values_for_contact(self, partner_id):
        if not partner_id:
            return
        fields_to_check_for_company = self._fields_to_check_for_company()
        fields_to_check_for_contact = self._fields_to_check_for_contact()
        res = {}
        for field, value in fields_to_check_for_contact:
            if getattr(partner_id, field) != value:
                if value != False:
                    res[field] = value
        if self.partner_name:
            # Create a company and link it to the person as the parent
            company_vals = {}
            for field, value in fields_to_check_for_company:
                if value != False:
                    company_vals[field] = value
            # company_vals['marketing_consensus'] = False
            company = self.env[RES_PARTNER].sudo().create(company_vals)
            res['parent_id'] = company.id
        return res

    # Task PES-27
    def _prepare_customer_values_with_parent(self, partner_id):
        if not partner_id or not partner_id.parent_id:
            return
        fields_to_check_for_company = self._fields_to_check_for_company()
        fields_to_check_for_contact = self._fields_to_check_for_contact()
        # fields_to_check_for_company = [
        #     item for item in fields_to_check_for_company if item[0] != 'marketing_consensus']
        company_vals = self._process_fields(
            fields_to_check_for_company, partner_id.parent_id)
        keys = []
        for key, value in company_vals.items():
            if partner_id.parent_id.mapped(key) and partner_id.parent_id.mapped(key)[0]:
                keys.append(key)
        if keys:
            for key in keys:
                del company_vals[key]
        partner_id.parent_id.sudo().write(company_vals)
        contact_vlas = self._process_fields(
            fields_to_check_for_contact, partner_id)
        return contact_vlas

    # Task PES-27
    def _prepare_customer_values_no_parent(self, partner_id):
        if not partner_id:
            return
        fields_to_check_for_company = [
            ('name', self.partner_name),
            # ('company_classification', self.company_classification.id),
            ('street', self.street),
            ('state_id', self.state_id.id),
            ('zip', self.zip),
            ('country_id', self.country_id.id),
            ('lang', self.lang_id.code),
            # ('marketing_consensus', self.marketing_consensus),
            ('website', self.website),
            ('user_id', self.user_id.id),
            ('team_id', self.team_id.id),
            ('city', self.city)
        ]
        fields_to_check_for_contact = self._fields_to_check_for_contact()
        res = {}
        fields_to_check = False

        if partner_id.company_type == 'person':
            fields_to_check = fields_to_check_for_contact

            res = self._process_fields(fields_to_check, partner_id)
            if self.partner_name:
                # company_vals = [
                #     item for item in fields_to_check_for_company if item[0] != 'marketing_consensus']
                company_vals = self._fields_to_check_for_company()
                company_id = self.env[RES_PARTNER].sudo().create(
                    dict(company_vals))
                res['parent_id'] = company_id.id if company_id else False

        contact_id = False
        if partner_id.company_type == 'company':
            fields_to_check = fields_to_check_for_company
            res = self._process_fields(fields_to_check, partner_id)
            keys = []
            for key, value in res.items():
                if partner_id.mapped(key) and partner_id.mapped(key)[0]:
                    keys.append(key)
            if keys:
                for key in keys:
                    del res[key]
            
            if self.contact_name:
                contact_vals = self._process_fields(
                    fields_to_check_for_contact, partner_id)
                contact_vals['parent_id'] = partner_id.id
                contact_id = self.env[RES_PARTNER].sudo().create(
                    contact_vals)

        return res, contact_id

    # Task PES-27
    def _process_fields(self, fields_to_check, partner_id):
        res = {}
        for field, value in fields_to_check:
            if getattr(partner_id, field) != value:
                if value != False:
                    res[field] = value
        return res

    # Task PES-27

    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        """Extract data from lead to create a partner.

        :param partner_name: future name of the partner
        :param is_company: True if the partner is a company
        :param parent_id: id of the parent partner (False if no parent)

        :return: dictionary of values to give at res_partner.create()
        """
        # Check if there is no existing partner_id
        if not self.partner_id:
            return

        # Split email parts using Odoo tools module
        email_parts = tools.email_split(self.email_from)

        # Determine if the existing partner is a company or a person
        is_company = True if self.partner_id.company_type == 'company' and not self.partner_id.parent_id else False
        is_person = True if self.partner_id.compa_prepare_customer_valuesny_type == 'person' and not self.partner_id.parent_id else False

        # Define fields to check for when creating a company or contact
        fields_to_check_for_company = self._fields_to_check_for_company()
        fields_to_check_for_contact = self._fields_to_check_for_contact()

        # Create/update partner based on whether it's a company or a person
        if is_company:
            # If partner_id is a company and vals is company only
            res = {}
            for field, value in fields_to_check_for_company:
                if getattr(self.partner_id, field) != value:
                    res[field] = value
            if self.contact_name:
                # Create contact and attach it to the company
                contact_vals = {}
                for field, value in fields_to_check_for_contact:
                    contact_vals[field] = value
                contact_vals['parent_id'] = self.partner_id.id
                contact_id = self.env[RES_PARTNER].sudo().create(
                    contact_vals)
                self.write({'partner_id': contact_id.id})
        elif is_person:
            res = {}
            for field, value in fields_to_check_for_contact:
                if getattr(self.partner_id, field) != value:
                    res[field] = value
            if partner_name:
                # Create a company and link it to the person as the parent
                company_vals = {}
                for field, value in fields_to_check_for_company:
                    company_vals[field] = value
                # company_vals['marketing_consensus'] = False
                company = self.env[RES_PARTNER].sudo().create(company_vals)
                res['parent_id'] = company.id
        else:
            # Update the parent company with new values
            company_vals = {}
            for field, value in fields_to_check_for_company:
                company_vals[field] = value
            # company_vals['marketing_consensus'] = False
            res = {}
            for field, value in fields_to_check_for_contact:
                if getattr(self.partner_id, field) != value:
                    res[field] = value
            self.partner_id.parent_id.write(company_vals)
        return res

    # Task PES-27
    def create_contact_action(self):
        if not self.partner_id:
            return self.env["ir.actions.actions"]._for_xml_id("ait_contact_from_lead.crm_create_partner_action")
