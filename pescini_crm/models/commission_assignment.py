# -*- coding: utf-8 -*-

from lxml import etree
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime, timedelta


COMMISSION_ASSIGNMENT = 'commission.assignment'
RES_PARTNER = 'res.partner'


class CommissionAssignment(models.Model):
    _name = COMMISSION_ASSIGNMENT
    _description = COMMISSION_ASSIGNMENT

    # Task PES-48
    name = fields.Char(string="Name",
                       default=lambda self: _('New Commission Assignment'))

    # Task PES-48
    agent = fields.Many2one(comodel_name="res.partner",
                            string="Agent",
                            domain=[('agent', '=', True)],
                            required=True)

    # Task PES-48
    has_priority = fields.Boolean(string="Precedenza",
                                  store=True,
                                  default=False)

    # Task PES-48
    company_classification_id = fields.Many2many(string="Company classification",
                                                 comodel_name="company.classification",
                                                 store=True,
                                                 readonly=False)
    # Task PES-48
    state_id = fields.Many2many(string="Provincia",
                                comodel_name="res.country.state",
                                store=True,
                                readonly=False)
    # Task PES-48
    company_id = fields.Many2one(comodel_name="res.company",
                                 string="Company",
                                 store=True)

    # Task PES-48

    def action_create_if_not_exist(self):        
        # Iterate through each record in the current recordset
        # Retrieve all commission assignments and agents with elevated privileges
        assignments = self.env[COMMISSION_ASSIGNMENT].sudo().search([])
        agents = self.env[RES_PARTNER].sudo().search(
            [('company_id', '=', self.env.company.id), ('agent', '=', True)])

        # Get the names of all agents
        agent_names = agents.mapped('name')

        # Remove names of agents already assigned to commission assignments
        for assign in assignments:
            if assign.agent.name in agent_names:
                agent_names.remove(assign.agent.name)

        # Iterate through remaining agent names to create new commission assignments
        for name in agent_names:
            # Filter the agents to get the one with the matching name
            agent_id = agents.filtered(lambda ag: ag.name == name)

            # Define values for the new commission assignment
            new_assignment_vals = {
                'name': _('New Commission Assignment'),
                'agent': agent_id.id,
                'has_priority': False,
                'company_classification_id': False,
                'state_id': False,
                'company_id': agents.company_id.id or self.env.company.id
            }

            # Create a new commission assignment with the specified values
            self.env[COMMISSION_ASSIGNMENT].sudo().create(
                new_assignment_vals)

    # Task PES-48

    def write(self, vals):
        # Check if 'has_priority' is present in the provided dictionary 'vals'
        if vals.get('has_priority'):
            # Retrieve all existing commission assignments for the same company excluding the current one
            assignments = self.env[COMMISSION_ASSIGNMENT].sudo().search(
                [('company_id', '=', self.company_id.id), ('id', '!=', self.id)])

            # Iterate through each assignment and update 'has_priority' to False
            for assign in assignments:
                assign.write({'has_priority': False})

        # Call the 'write' method of the superclass to perform the actual write operation
        return super().write(vals)

    # Task PES-48

    @api.model
    def create(self, vals_list):
        """
        Override of the create method to customize the creation of CommissionAssignment records.

        Explanation:
        - Calls the create method of the superclass (super) to create the record.
        - Checks if the created record has a company_id.
        - If not, sets the company_id based on the agent's company_id or the default company_id from the environment.
        - Returns the created record.
        """
        # Call the create method of the superclass to create the record
        res = super(CommissionAssignment, self).create(vals_list)

        # Check if the created record has a company_id
        if not res.company_id:
            # Set the company_id based on the agent's company_id or the default company_id from the environment
            res.company_id = res.agent.company_id.id or self.env.company.id

        # Return the created record
        return res

    # Task PES-48

    def action_add_all(self):
        """
        This method is responsible for adding all available company classifications to the current record.

        Explanation:
        - It retrieves all company classifications using a search on 'company.classification'.
        - It extracts the IDs of the retrieved company classifications.
        - It sets the 'company_classification_id' field of the current record with the list of company classification IDs.

        Note: This assumes that 'company_classification_id' is a Many2many field.

        Example Usage:
        self.action_add_all()
        """
        for record in self:
            # Retrieve all company classifications
            company_classification = self.env['company.classification'].sudo().search([
            ])

            # Extract the IDs of the retrieved company classifications
            company_classification_ids = company_classification.mapped('id')

            # Set the 'company_classification_id' field of the current record
            record.company_classification_id = [
                (6, 0, company_classification_ids)]
