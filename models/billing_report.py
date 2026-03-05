from odoo import models, fields, api


class BillingReport(models.Model):
    _name = 'openai.billing.report'
    _description = 'Monthly Expenditure Report'
    _order = 'period_start desc'

    name = fields.Char(
        string='Report Name', compute='_compute_name', store=True)
    org_unit_id = fields.Many2one(
        'openai.billing.org_unit', string='Department',
        help='Leave empty for all departments')
    period_start = fields.Date(string='Period Start', required=True)
    period_end = fields.Date(string='Period End', required=True)
    report_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('weekly', 'Weekly'),
        ('custom', 'Custom Period'),
    ], string='Report Type', default='monthly', required=True)

    total_tokens = fields.Integer(
        string='Total Tokens', compute='_compute_totals', store=True)
    total_cost = fields.Float(
        string='Total Cost (USD)', compute='_compute_totals',
        store=True, digits=(16, 4))
    total_requests = fields.Integer(
        string='Total Requests', compute='_compute_totals', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('sent', 'Sent'),
    ], string='Status', default='draft', required=True)

    # ------------------------------------------------------------------
    # Computed helpers
    # ------------------------------------------------------------------
    @api.depends('org_unit_id', 'period_start', 'report_type')
    def _compute_name(self):
        type_map = {
            'monthly': 'Monthly',
            'weekly': 'Weekly',
            'custom': 'Custom',
        }
        for rec in self:
            dept = (rec.org_unit_id.name
                    if rec.org_unit_id else 'All Departments')
            start = (rec.period_start.strftime('%b %Y')
                     if rec.period_start else '')
            label = type_map.get(rec.report_type, '')
            rec.name = f"{dept} – {label} Report – {start}"

    @api.depends('org_unit_id', 'period_start', 'period_end')
    def _compute_totals(self):
        for rec in self:
            logs = rec._get_usage_logs()
            rec.total_tokens = sum(logs.mapped('total_tokens'))
            rec.total_cost = sum(logs.mapped('cost_usd'))
            rec.total_requests = len(logs)

    def _get_usage_logs(self):
        """Return the usage-log recordset for this report's scope."""
        self.ensure_one()
        domain = [
            ('request_timestamp', '>=',
             fields.Datetime.to_string(self.period_start)),
            ('request_timestamp', '<=',
             fields.Datetime.to_string(self.period_end)),
        ]
        if self.org_unit_id:
            domain.append(('org_unit_id', '=', self.org_unit_id.id))
        return self.env['openai.billing.usage_log'].search(
            domain, order='request_timestamp asc', limit=500)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_generate(self):
        self.write({'state': 'generated'})

    def action_download_pdf(self):
        return self.env.ref(
            'openai_billing.action_report_monthly_expenditure'
        ).report_action(self)

    def action_download_csv(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': f'{base_url}/openai_billing/export/csv?report_id={self.id}',
            'target': 'new',
        }
