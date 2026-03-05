from odoo import models, fields, api


class ApiKey(models.Model):
    _name = 'openai.billing.api_key'
    _description = 'API Key'
    _order = 'name'

    name = fields.Char(string='Key Name', required=True)
    key_value = fields.Char(
        string='API Key', required=True,
        help='The OpenAI API key (sk-…)')
    org_unit_id = fields.Many2one(
        'openai.billing.org_unit', string='Department',
        required=True, ondelete='restrict')
    user_id = fields.Many2one(
        'res.users', string='Assigned User', required=True)
    category = fields.Selection([
        ('production', 'Production'),
        ('development', 'Development'),
        ('testing', 'Testing'),
        ('research', 'Research'),
    ], string='Category', default='development', required=True)
    application_name = fields.Char(string='Application / Use Case')
    state = fields.Selection([
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('revoked', 'Revoked'),
    ], string='Status', default='active', required=True)

    usage_log_ids = fields.One2many(
        'openai.billing.usage_log', 'api_key_id', string='Usage Logs')
    notes = fields.Text(string='Notes')

    # Computed totals
    total_usage_tokens = fields.Integer(
        string='Total Tokens Used', compute='_compute_total_usage')
    total_cost = fields.Float(
        string='Total Cost (USD)', compute='_compute_total_usage',
        digits=(16, 4))

    def _compute_total_usage(self):
        for rec in self:
            logs = rec.usage_log_ids
            rec.total_usage_tokens = sum(logs.mapped('total_tokens'))
            rec.total_cost = sum(logs.mapped('cost_usd'))

    def action_suspend(self):
        self.write({'state': 'suspended'})

    def action_revoke(self):
        self.write({'state': 'revoked'})

    def action_activate(self):
        self.write({'state': 'active'})
