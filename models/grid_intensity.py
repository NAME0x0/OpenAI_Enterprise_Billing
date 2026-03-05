from odoo import models, fields


class GridIntensity(models.Model):
    _name = 'openai.billing.grid_intensity'
    _description = 'Data Centre Grid Carbon Intensity'
    _order = 'name'

    name = fields.Char(
        string='Region / Grid', required=True,
        help='Data centre region name (e.g., US East - Virginia)')
    co2g_per_kwh = fields.Float(
        string='CO₂ Intensity (gCO₂/kWh)', digits=(10, 4), required=True,
        help='Grams of CO₂ emitted per kilowatt-hour of electricity '
             'consumed in this grid region')
    pue = fields.Float(
        string='PUE (Power Usage Effectiveness)', digits=(4, 2),
        default=1.10,
        help='Data centre Power Usage Effectiveness. '
             'Industry average ≈ 1.58; hyperscale best-in-class ≈ 1.10. '
             'Multiplied with raw compute energy to get total facility energy.')
    renewable_pct = fields.Float(
        string='Renewable Energy %', digits=(5, 1), default=0.0,
        help='Percentage of grid electricity sourced from renewables. '
             'Used to compute net (market-based) emissions.')
    notes = fields.Text(
        string='Source / Notes',
        help='Citation or reference for the carbon intensity data')
