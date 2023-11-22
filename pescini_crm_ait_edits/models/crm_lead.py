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
                res = self._prepare_both_existing(
                    force_partner, force_company_id)
                # Task PES-27
                res['marketing_consensus'] = self.marketing_consensus
                force_company_id.company_classification = self.company_classification.id

            elif force_partner_id and not force_company_id:
                force_partner = self.env[RES_PARTNER].sudo().browse(
                    force_partner_id)
                if force_partner and force_partner.parent_id:
                    res = self._prepare_customer_values_with_parent(
                        force_partner)
                    # Task PES-27
                    res['marketing_consensus'] = self.marketing_consensus
                    force_partner.parent_id.company_classification = self.company_classification.id
                else:
                    res, contact_id = self._prepare_customer_values_no_parent(
                        force_partner)
                    # Task PES-27
                    if contact_id:
                        contact_id.marketing_consensus = lead.marketing_consensus
                    else:
                        res['marketing_consensus'] = lead.marketing_consensus
                    if lead.company_classification:
                        res['company_classification'] = lead.company_classification.id

            lead.partner_id = contact_id.id if contact_id else force_partner_id
            if 'lang_id' in res.keys():
                lang = res['lang_id']
                del res['lang_id']
                res['lang'] = lang
            lead.partner_id.write(res) if res else False
            if not lead.partner_id and create_missing:
                partner = lead._create_customer()
                # Task PES-27                
                if not partner.parent_id:
                    partner.company_classification = self.company_classification.id
                else:
                    partner.parent_id.company_classification = self.company_classification.id
                    partner.parent_id.marketing_consensus = False
                partner.marketing_consensus = self.marketing_consensus
                lead.partner_id = partner.id
