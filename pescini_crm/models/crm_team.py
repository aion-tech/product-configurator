# -*- coding: utf-8 -*-
import datetime
import logging
import random
import threading

from ast import literal_eval

from odoo import api, exceptions, fields, models, _
from odoo.osv import expression
from odoo.tools import float_compare, float_round
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


CRM_TEAM = 'crm.team'


class CrmLead(models.Model):
    _inherit = CRM_TEAM
    _description = CRM_TEAM

    # Task PES-63
    agent_ids = fields.Many2many(comodel_name="res.partner",
                                 string="Agents",
                                 domain="[('agent', '=', True)]")

    # Task PES-81
    def _allocate_leads(self, work_days=1):
        """ Allocate leads to teams given by self. This method sets ``team_id``
        field on lead records that are unassigned (no team and no responsible).
        No salesperson is assigned in this process. Its purpose is simply to
        allocate leads within teams.

        This process allocates all available leads on teams weighted by their
        maximum assignment by month that indicates their relative workload.

        Heuristic of this method is the following:
          * find unassigned leads for each team, aka leads being
            * without team, without user -> not assigned;
            * not in a won stage, and not having False/0 (lost) or 100 (won)
              probability) -> live leads;
            * if set, a delay after creation can be applied (see BUNDLE_HOURS_DELAY)
              parameter explanations here below;
            * matching the team's assignment domain (empty means
              everything);

          * assign a weight to each team based on their assignment_max that
            indicates their relative workload;

          * pick a random team using a weighted random choice and find a lead
            to assign:

            * remove already assigned leads from the available leads. If there
              is not any lead spare to assign, remove team from active teams;
            * pick the first lead and set the current team;
            * when setting a team on leads, leads are also merged with their
              duplicates. Purpose is to clean database and avoid assigning
              duplicates to same or different teams;
            * add lead and its duplicates to already assigned leads;

          * pick another random team until their is no more leads to assign
            to any team;

        This process ensure that teams having overlapping domains will all
        receive leads as lead allocation is done one lead at a time. This
        allocation will be proportional to their size (assignment of their
        members).

        :config int crm.assignment.bundle: deprecated
        :config int crm.assignment.commit.bundle: optional config parameter allowing
          to set size of lead batch to be committed together. By default 100
          which is a good trade-off between transaction time and speed
        :config int crm.assignment.delay: optional config parameter giving a
          delay before taking a lead into assignment process (BUNDLE_HOURS_DELAY)
          given in hours. Purpose if to allow other crons or automated actions
          to make their job. This option is mainly historic as its purpose was
          to let automated actions prepare leads and score before PLS was added
          into CRM. This is now not required anymore but still supported;

        :param float work_days: see ``CrmTeam.action_assign_leads()``;

        :return teams_data: dict() with each team assignment result:
          team: {
            'assigned': set of lead IDs directly assigned to the team (no
              duplicate or merged found);
            'merged': set of lead IDs merged and assigned to the team (main
              leads being results of merge process);
            'duplicates': set of lead IDs found as duplicates and merged into
              other leads. Those leads are unlinked during assign process and
              are already removed at return of this method;
          }, ...
        """
        if work_days < 0.2 or work_days > 30:
            raise ValueError(
                _('Leads team allocation should be done for at least 0.2 or maximum 30 work days, not %.2f.', work_days)
            )

        BUNDLE_HOURS_DELAY = int(self.env['ir.config_parameter'].sudo().get_param('crm.assignment.delay', default=0))
        BUNDLE_COMMIT_SIZE = int(self.env['ir.config_parameter'].sudo().get_param('crm.assignment.commit.bundle', 100))
        auto_commit = not getattr(threading.current_thread(), 'testing', False)

        # leads
        max_create_dt = self.env.cr.now() - datetime.timedelta(hours=BUNDLE_HOURS_DELAY)
        duplicates_lead_cache = dict()

        # teams data
        teams_data, population, weights = dict(), list(), list()
        for team in self:
            if not team.assignment_max:
                continue

            # Task PES-81
            lead_domain = expression.AND([
                literal_eval(team.assignment_domain or '[]'),
                [('create_date', '<=', max_create_dt)],
                ['&', ('team_id', '=', False), ('user_id', '=', False)],
                ['|', ('stage_id', '=', False), ('stage_id.is_won', '=', False)],
                [('company_id', '=', team.company_id.id)]
            ])

            leads = self.env["crm.lead"].search(lead_domain)
            # Fill duplicate cache: search for duplicate lead before the assignation
            # avoid to flush during the search at every assignation
            for lead in leads:
                if lead not in duplicates_lead_cache:
                    duplicates_lead_cache[lead] = lead._get_lead_duplicates(email=lead.email_from)

            teams_data[team] = {
                "team": team,
                "leads": leads,
                "assigned": set(),
                "merged": set(),
                "duplicates": set(),
            }
            population.append(team)
            weights.append(team.assignment_max)

        # Start a new transaction, since data fetching take times
        # and the first commit occur at the end of the bundle,
        # the first transaction can be long which we want to avoid
        if auto_commit:
            self._cr.commit()

        # assignment process data
        global_data = dict(assigned=set(), merged=set(), duplicates=set())
        leads_done_ids, lead_unlink_ids, counter = set(), set(), 0
        while population:
            counter += 1
            team = random.choices(population, weights=weights, k=1)[0]

            # filter remaining leads, remove team if no more leads for it
            teams_data[team]["leads"] = teams_data[team]["leads"].filtered(lambda l: l.id not in leads_done_ids).exists()
            if not teams_data[team]["leads"]:
                population_index = population.index(team)
                population.pop(population_index)
                weights.pop(population_index)
                continue

            # assign + deduplicate and concatenate results in teams_data to keep some history
            candidate_lead = teams_data[team]["leads"][0]
            assign_res = team._allocate_leads_deduplicate(candidate_lead, duplicates_cache=duplicates_lead_cache)
            for key in ('assigned', 'merged', 'duplicates'):
                teams_data[team][key].update(assign_res[key])
                leads_done_ids.update(assign_res[key])
                global_data[key].update(assign_res[key])
            lead_unlink_ids.update(assign_res['duplicates'])

            # auto-commit except in testing mode. As this process may be time consuming or we
            # may encounter errors, already commit what is allocated to avoid endless cron loops.
            if auto_commit and counter % BUNDLE_COMMIT_SIZE == 0:
                # unlink duplicates once
                self.env['crm.lead'].browse(lead_unlink_ids).unlink()
                lead_unlink_ids = set()
                self._cr.commit()

        # unlink duplicates once
        self.env['crm.lead'].browse(lead_unlink_ids).unlink()

        if auto_commit:
            self._cr.commit()

        # some final log
        _logger.info('## Assigned %s leads', (len(global_data['assigned']) + len(global_data['merged'])))
        for team, team_data in teams_data.items():
            _logger.info(
                '## Assigned %s leads to team %s',
                len(team_data['assigned']) + len(team_data['merged']), team.id)
            _logger.info(
                '\tLeads: direct assign %s / merge result %s / duplicates merged: %s',
                team_data['assigned'], team_data['merged'], team_data['duplicates'])
        return teams_data