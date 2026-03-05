from odoo import models, fields, api
from datetime import date


class OrgUnit(models.Model):
    _name = 'openai.billing.org_unit'
    _description = 'Organisational Unit / Department'
    _order = 'name'

    name = fields.Char(string='Department Name', required=True)
    code = fields.Char(string='Department Code', required=True)
    parent_id = fields.Many2one(
        'openai.billing.org_unit', string='Parent Department',
        ondelete='restrict')
    child_ids = fields.One2many(
        'openai.billing.org_unit', 'parent_id', string='Sub-departments')
    manager_id = fields.Many2one('res.users', string='Department Manager')
    monthly_token_quota = fields.Integer(
        string='Monthly Token Quota', required=True, default=100000)
    hard_limit_enabled = fields.Boolean(
        string='Enable Hard Limit', default=True,
        help='Automatically suspend API access when quota is reached')
    state = fields.Selection([
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('archived', 'Archived'),
    ], string='Status', default='active', required=True)

    # Computed usage fields
    current_month_usage = fields.Integer(
        string='Current Month Usage (Tokens)',
        compute='_compute_current_usage', store=False)
    current_month_cost = fields.Float(
        string='Current Month Cost (USD)',
        compute='_compute_current_usage', store=False, digits=(16, 4))
    usage_percentage = fields.Float(
        string='Usage %',
        compute='_compute_current_usage', store=False)

    # Model access control
    allowed_model_ids = fields.Many2many(
        'openai.billing.ai_model', string='Allowed AI Models',
        help='Leave empty to allow all models. Select specific models to restrict access.')

    # Alert tracking
    alert_80_sent_date = fields.Date(string='80% Alert Sent Date')
    alert_90_sent_date = fields.Date(string='90% Alert Sent Date')

    # Related
    api_key_ids = fields.One2many(
        'openai.billing.api_key', 'org_unit_id', string='API Keys')
    project_tag_ids = fields.One2many(
        'openai.billing.project_tag', 'org_unit_id', string='Project Tags')

    notes = fields.Text(string='Notes')

    _code_unique = models.Constraint(
        'unique(code)',
        'Department code must be unique!')
    _quota_positive = models.Constraint(
        'CHECK(monthly_token_quota > 0)',
        'Monthly token quota must be positive!')

    def _compute_current_usage(self):
        today = date.today()
        first_of_month = today.replace(day=1)
        for rec in self:
            logs = self.env['openai.billing.usage_log'].search([
                ('org_unit_id', '=', rec.id),
                ('request_timestamp', '>=',
                 fields.Datetime.to_string(first_of_month)),
            ])
            rec.current_month_usage = sum(logs.mapped('total_tokens'))
            rec.current_month_cost = sum(logs.mapped('cost_usd'))
            if rec.monthly_token_quota:
                rec.usage_percentage = (
                    rec.current_month_usage / rec.monthly_token_quota)
            else:
                rec.usage_percentage = 0.0

    def action_suspend(self):
        """Suspend API access for this department."""
        for rec in self:
            self.env['openai.billing.audit_trail'].sudo().create({
                'action_type': 'suspension',
                'org_unit_id': rec.id,
                'performed_by': self.env.uid,
                'old_value': rec.state,
                'new_value': 'suspended',
                'description': (
                    f'Department {rec.name} suspended '
                    f'– quota limit reached'),
            })
            rec.state = 'suspended'

    def action_reactivate(self):
        """Reactivate a suspended department."""
        for rec in self:
            self.env['openai.billing.audit_trail'].sudo().create({
                'action_type': 'override',
                'org_unit_id': rec.id,
                'performed_by': self.env.uid,
                'old_value': rec.state,
                'new_value': 'active',
                'description': (
                    f'Department {rec.name} reactivated by administrator'),
            })
            rec.state = 'active'

    def write(self, vals):
        # Track quota changes in the audit trail
        if 'monthly_token_quota' in vals:
            for rec in self:
                old_val = rec.monthly_token_quota
                new_val = vals['monthly_token_quota']
                if old_val != new_val:
                    self.env['openai.billing.audit_trail'].sudo().create({
                        'action_type': 'quota_change',
                        'org_unit_id': rec.id,
                        'performed_by': self.env.uid,
                        'old_value': str(old_val),
                        'new_value': str(new_val),
                        'description': (
                            f'Quota changed from {old_val:,} '
                            f'to {new_val:,} tokens'),
                    })
        return super().write(vals)

    # ------------------------------------------------------------------
    # Cron methods
    # ------------------------------------------------------------------
    def _cron_check_quotas(self):
        """Hourly cron: check all active org-units for quota thresholds."""
        today = date.today()
        units = self.search([('state', '=', 'active')])
        for unit in units:
            if unit.monthly_token_quota <= 0:
                continue
            pct = unit.usage_percentage * 100  # stored as 0–1

            # 100 % – suspend if hard limit is enabled
            if pct >= 100 and unit.hard_limit_enabled:
                unit.action_suspend()
                self.env['openai.billing.quota_alert'].create({
                    'org_unit_id': unit.id,
                    'alert_type': 'limit_reached',
                    'usage_at_alert': unit.current_month_usage,
                    'quota_at_alert': unit.monthly_token_quota,
                    'percentage': pct,
                })
            # 90 % warning
            elif pct >= 90 and unit.alert_90_sent_date != today:
                unit.alert_90_sent_date = today
                self.env['openai.billing.quota_alert'].create({
                    'org_unit_id': unit.id,
                    'alert_type': 'warning_90',
                    'usage_at_alert': unit.current_month_usage,
                    'quota_at_alert': unit.monthly_token_quota,
                    'percentage': pct,
                })
            # 80 % warning
            elif pct >= 80 and unit.alert_80_sent_date != today:
                unit.alert_80_sent_date = today
                self.env['openai.billing.quota_alert'].create({
                    'org_unit_id': unit.id,
                    'alert_type': 'warning_80',
                    'usage_at_alert': unit.current_month_usage,
                    'quota_at_alert': unit.monthly_token_quota,
                    'percentage': pct,
                })

    def _cron_reset_monthly_alerts(self):
        """Monthly cron: reset alert flags on 1st of the month."""
        units = self.search([])
        units.write({
            'alert_80_sent_date': False,
            'alert_90_sent_date': False,
        })
        # Auto-reactivate hard-limited departments
        suspended = self.search([
            ('state', '=', 'suspended'),
            ('hard_limit_enabled', '=', True),
        ])
        for unit in suspended:
            self.env['openai.billing.audit_trail'].sudo().create({
                'action_type': 'override',
                'org_unit_id': unit.id,
                'performed_by': self.env.ref('base.user_admin').id,
                'old_value': 'suspended',
                'new_value': 'active',
                'description': (
                    'Auto-reactivated at start of new billing period'),
            })
            unit.state = 'active'
