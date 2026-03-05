from odoo import models, fields


class QuotaAlert(models.Model):
    _name = 'openai.billing.quota_alert'
    _description = 'Quota Threshold Alert'
    _order = 'create_date desc'

    org_unit_id = fields.Many2one(
        'openai.billing.org_unit', string='Department', required=True)
    alert_type = fields.Selection([
        ('warning_80', '80 % Threshold Warning'),
        ('warning_90', '90 % Threshold Warning'),
        ('limit_reached', '100 % – Limit Reached'),
    ], string='Alert Type', required=True)
    usage_at_alert = fields.Integer(string='Usage at Alert (Tokens)')
    quota_at_alert = fields.Integer(string='Quota at Alert (Tokens)')
    percentage = fields.Float(string='Usage %', digits=(5, 1))
    state = fields.Selection([
        ('sent', 'Sent'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
    ], string='Status', default='sent', required=True)
    acknowledged_by = fields.Many2one('res.users', string='Acknowledged By')
    resolution_notes = fields.Text(string='Resolution Notes')

    def action_acknowledge(self):
        self.write({
            'state': 'acknowledged',
            'acknowledged_by': self.env.uid,
        })

    def action_resolve(self):
        self.write({'state': 'resolved'})
