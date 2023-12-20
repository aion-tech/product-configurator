# -*- coding: utf-8 -*-
import logging
import pytz
import threading
from collections import OrderedDict, defaultdict
from datetime import date, datetime, timedelta
from psycopg2 import sql

from odoo import api, fields, models, tools, SUPERUSER_ID, _

_logger = logging.getLogger(__name__)

CRM_TEAM = 'crm.team'


class CrmLead(models.Model):
    _inherit = CRM_TEAM
    _description = CRM_TEAM

    # Task PES-63
    agent_ids = fields.Many2many(comodel_name="res.partner",
                                 string="Agents",
                                 domain="[('agent', '=', True)]")