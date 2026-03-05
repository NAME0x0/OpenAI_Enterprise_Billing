from odoo import models, fields, api


class ProjectTag(models.Model):
    _name = 'openai.billing.project_tag'
    _description = 'Project Tag for Cost Attribution'
    _order = 'name'

    name = fields.Char(string='Project Name', required=True)
    code = fields.Char(string='Project Code', required=True)
    org_unit_id = fields.Many2one(
        'openai.billing.org_unit', string='Department', required=True)
    description = fields.Text(string='Description')
    is_active = fields.Boolean(string='Active', default=True)

    usage_log_ids = fields.One2many(
        'openai.billing.usage_log', 'project_tag_id', string='Usage Logs')

    # Computed totals
    total_tokens = fields.Integer(
        string='Total Tokens', compute='_compute_totals')
    total_cost = fields.Float(
        string='Total Cost (USD)', compute='_compute_totals',
        digits=(16, 4))

    _code_unique = models.Constraint(
        'unique(code)',
        'Project code must be unique!')

    def _compute_totals(self):
        for rec in self:
            logs = rec.usage_log_ids
            rec.total_tokens = sum(logs.mapped('total_tokens'))
            rec.total_cost = sum(logs.mapped('cost_usd'))
