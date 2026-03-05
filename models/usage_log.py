from odoo import models, fields, api


class UsageLog(models.Model):
    _name = 'openai.billing.usage_log'
    _description = 'API Usage Transaction Log'
    _order = 'request_timestamp desc'

    api_key_id = fields.Many2one(
        'openai.billing.api_key', string='API Key',
        required=True, ondelete='restrict')
    org_unit_id = fields.Many2one(
        'openai.billing.org_unit', string='Department',
        related='api_key_id.org_unit_id', store=True, readonly=True)
    user_id = fields.Many2one(
        'res.users', string='Requesting User', required=True)
    ai_model_id = fields.Many2one(
        'openai.billing.ai_model', string='Model Used', required=True)
    project_tag_id = fields.Many2one(
        'openai.billing.project_tag', string='Project Tag')

    prompt_tokens = fields.Integer(string='Prompt Tokens', required=True)
    completion_tokens = fields.Integer(
        string='Completion Tokens', required=True)
    total_tokens = fields.Integer(
        string='Total Tokens', compute='_compute_totals', store=True)
    cost_usd = fields.Float(
        string='Cost (USD)', compute='_compute_totals',
        store=True, digits=(16, 6))

    # Energy & carbon fields (computed from model benchmarks)
    energy_consumed_kwh = fields.Float(
        string='Energy Consumed (kWh)',
        compute='_compute_energy', store=True, digits=(12, 10),
        help='Estimated energy consumed for this request')
    co2_emissions_g = fields.Float(
        string='CO₂ Emissions (g)',
        compute='_compute_energy', store=True, digits=(12, 6),
        help='Estimated grams of CO₂ emitted for this request')

    # Benchmark snapshots (frozen at creation)
    benchmark_energy_kwh_per_1k = fields.Float(
        string='Energy Benchmark (kWh/1K tokens)',
        digits=(16, 10), readonly=True,
        help='Snapshot of model energy_kwh_per_1k_tokens at record creation')
    benchmark_grid_co2g_kwh = fields.Float(
        string='Grid CO₂ Benchmark (gCO₂/kWh)',
        digits=(10, 4), readonly=True,
        help='Snapshot of grid intensity at record creation')
    benchmark_pue = fields.Float(
        string='PUE Benchmark', digits=(4, 2), readonly=True,
        help='Snapshot of data centre PUE at record creation')

    request_timestamp = fields.Datetime(
        string='Request Timestamp', required=True,
        default=fields.Datetime.now)
    purpose_category = fields.Selection([
        ('inference', 'Inference / Chat'),
        ('embedding', 'Embedding'),
        ('fine_tuning', 'Fine-tuning'),
        ('image_gen', 'Image Generation'),
        ('code_gen', 'Code Generation'),
        ('data_analysis', 'Data Analysis'),
        ('support', 'Customer Support'),
        ('internal', 'Internal Operations'),
    ], string='Purpose', default='inference', required=True)

    @api.depends(
        'prompt_tokens', 'completion_tokens',
        'ai_model_id.cost_per_prompt_token_usd',
        'ai_model_id.cost_per_completion_token_usd')
    def _compute_totals(self):
        for rec in self:
            rec.total_tokens = rec.prompt_tokens + rec.completion_tokens
            prompt_cost = (
                rec.prompt_tokens *
                (rec.ai_model_id.cost_per_prompt_token_usd or 0))
            completion_cost = (
                rec.completion_tokens *
                (rec.ai_model_id.cost_per_completion_token_usd or 0))
            rec.cost_usd = prompt_cost + completion_cost

    @api.depends('total_tokens', 'benchmark_energy_kwh_per_1k',
                 'benchmark_grid_co2g_kwh', 'benchmark_pue')
    def _compute_energy(self):
        for rec in self:
            energy_kwh = rec.benchmark_energy_kwh_per_1k or 0.0
            pue = rec.benchmark_pue or 1.0
            total = rec.total_tokens or 0
            # Energy = (total_tokens / 1000) * energy_per_1k * PUE
            rec.energy_consumed_kwh = (total / 1000.0) * energy_kwh * pue
            # CO₂ = energy_kwh * grid_intensity
            rec.co2_emissions_g = (
                rec.energy_consumed_kwh *
                (rec.benchmark_grid_co2g_kwh or 0.0))

    @api.model_create_multi
    def create(self, vals_list):
        """Snapshot energy benchmarks at creation time for immutability."""
        for vals in vals_list:
            model_id = vals.get('ai_model_id')
            if model_id and not vals.get('benchmark_energy_kwh_per_1k'):
                ai_model = self.env['openai.billing.ai_model'].browse(
                    model_id)
                # Energy benchmark
                vals['benchmark_energy_kwh_per_1k'] = (
                    ai_model.energy_kwh_per_1k_tokens or 0.0)
                # Grid intensity — model-level, then global average
                grid = ai_model.grid_intensity_id
                if grid:
                    vals['benchmark_grid_co2g_kwh'] = grid.co2g_per_kwh
                    vals['benchmark_pue'] = grid.pue or 1.10
                else:
                    # Default: US average grid + hyperscale PUE
                    vals.setdefault('benchmark_grid_co2g_kwh', 372.0)
                    vals.setdefault('benchmark_pue', 1.10)
        return super().create(vals_list)
