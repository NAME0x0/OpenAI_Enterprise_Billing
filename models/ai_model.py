from odoo import models, fields, api


class AiModel(models.Model):
    _name = 'openai.billing.ai_model'
    _description = 'AI Model Registry'
    _order = 'name'

    name = fields.Char(string='Model Name', required=True)
    model_key = fields.Char(
        string='API Model Key', required=True,
        help='The model identifier used in API calls (e.g., gpt-4.1)')
    model_type = fields.Selection([
        ('chat', 'Chat / Completion'),
        ('reasoning', 'Reasoning'),
        ('image', 'Image Generation'),
        ('audio', 'Audio'),
        ('embedding', 'Embedding'),
        ('code', 'Code / Codex'),
    ], string='Type', default='chat', required=True)
    model_tier = fields.Selection([
        ('flagship', 'Flagship'),
        ('standard', 'Standard'),
        ('mini', 'Mini'),
        ('nano', 'Nano'),
        ('legacy', 'Legacy'),
    ], string='Tier', default='standard')
    cost_per_prompt_token_usd = fields.Float(
        string='Cost per Prompt Token (USD)', digits=(16, 10))
    cost_per_completion_token_usd = fields.Float(
        string='Cost per Completion Token (USD)', digits=(16, 10))
    cost_prompt_display = fields.Char(
        string='Prompt Cost ($/1M tokens)',
        compute='_compute_cost_display', store=True)
    cost_completion_display = fields.Char(
        string='Completion Cost ($/1M tokens)',
        compute='_compute_cost_display', store=True)

    # Energy / sustainability fields
    energy_kwh_per_1k_tokens = fields.Float(
        string='Energy per 1K Tokens (kWh)', digits=(16, 10),
        help='Estimated energy consumed in kWh per 1,000 total tokens '
             '(based on published inference benchmarks)')
    grid_intensity_id = fields.Many2one(
        'openai.billing.grid_intensity',
        string='Data Centre Grid Region',
        help='Grid carbon intensity for this model\'s primary data centre. '
             'Used to compute CO₂ emissions per request.')

    is_active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')
    context_window = fields.Integer(
        string='Context Window (tokens)',
        help='Maximum context window size in tokens')
    release_date = fields.Date(string='Release Date')

    @api.depends('cost_per_prompt_token_usd', 'cost_per_completion_token_usd')
    def _compute_cost_display(self):
        for rec in self:
            if rec.cost_per_prompt_token_usd:
                per_million = rec.cost_per_prompt_token_usd * 1_000_000
                rec.cost_prompt_display = f"${per_million:.2f}"
            else:
                rec.cost_prompt_display = "$0.00"
            if rec.cost_per_completion_token_usd:
                per_million = rec.cost_per_completion_token_usd * 1_000_000
                rec.cost_completion_display = f"${per_million:.2f}"
            else:
                rec.cost_completion_display = "$0.00"
