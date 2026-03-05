from odoo import http
from odoo.http import request
from datetime import date, timedelta


class OpenAIBillingDashboard(http.Controller):
    """Endpoints that feed the OWL billing dashboard."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _date_range(period):
        today = date.today()
        if period == 'this_month':
            start = today.replace(day=1)
        elif period == 'last_30_days':
            start = today - timedelta(days=30)
        elif period == 'this_quarter':
            quarter_month = ((today.month - 1) // 3) * 3 + 1
            start = today.replace(month=quarter_month, day=1)
        elif period == 'last_year':
            start = today - timedelta(days=365)
        elif period == 'all_time':
            start = date(2020, 1, 1)
        else:
            start = today.replace(day=1)
        return start, today

    # ------------------------------------------------------------------
    # KPIs
    # ------------------------------------------------------------------
    @http.route('/openai_billing/dashboard/kpis',
                type='jsonrpc', auth='user')
    def get_kpis(self, date_filter='this_month'):
        start, end = self._date_range(date_filter)
        UsageLog = request.env['openai.billing.usage_log'].sudo()
        OrgUnit = request.env['openai.billing.org_unit'].sudo()

        domain = [
            ('request_timestamp', '>=', str(start)),
            ('request_timestamp', '<=', str(end)),
        ]
        logs = UsageLog.search(domain)

        total_tokens = sum(logs.mapped('total_tokens'))
        total_cost = sum(logs.mapped('cost_usd'))
        total_requests = len(logs)

        # Energy & carbon metrics
        total_energy_kwh = sum(logs.mapped('energy_consumed_kwh'))
        total_co2_g = sum(logs.mapped('co2_emissions_g'))
        energy_per_request = (
            total_energy_kwh / total_requests if total_requests else 0)

        # Try to resolve the primary grid region name
        grid_region = 'US Average'
        try:
            grid = request.env['openai.billing.grid_intensity'].sudo().search(
                [], limit=1, order='id')
            if grid:
                grid_region = grid.name
        except Exception:
            pass

        active_depts = OrgUnit.search_count([('state', '=', 'active')])
        suspended_depts = OrgUnit.search_count([('state', '=', 'suspended')])
        active_keys = request.env['openai.billing.api_key'].sudo().search_count(
            [('state', '=', 'active')])

        total_budget = sum(
            OrgUnit.search([('state', '=', 'active')])
            .mapped('monthly_token_quota'))

        return {
            'total_tokens': total_tokens,
            'total_cost': round(total_cost, 2),
            'total_requests': total_requests,
            'total_energy_kwh': round(total_energy_kwh, 6),
            'total_co2_g': round(total_co2_g, 2),
            'energy_per_request': round(energy_per_request, 6),
            'grid_region': grid_region,
            'active_departments': active_depts,
            'suspended_departments': suspended_depts,
            'active_api_keys': active_keys,
            'total_budget_tokens': total_budget,
            'budget_utilization': (
                round(total_tokens / total_budget * 100, 1)
                if total_budget else 0),
        }

    # ------------------------------------------------------------------
    # Chart data
    # ------------------------------------------------------------------
    @http.route('/openai_billing/dashboard/charts',
                type='jsonrpc', auth='user')
    def get_chart_data(self, date_filter='this_month'):
        start, end = self._date_range(date_filter)
        UsageLog = request.env['openai.billing.usage_log'].sudo()
        domain = [
            ('request_timestamp', '>=', str(start)),
            ('request_timestamp', '<=', str(end)),
        ]
        logs = UsageLog.search(domain)

        # ---- Cost by department ----
        dept_costs = {}
        for log in logs:
            dept = log.org_unit_id.name or 'Unassigned'
            dept_costs[dept] = dept_costs.get(dept, 0) + log.cost_usd

        # ---- Token usage by model ----
        model_usage = {}
        for log in logs:
            model = log.ai_model_id.name or 'Unknown'
            model_usage[model] = model_usage.get(model, 0) + log.total_tokens

        # ---- Cost by purpose ----
        purpose_labels = dict(
            UsageLog._fields['purpose_category'].selection)
        purpose_costs = {}
        for log in logs:
            label = purpose_labels.get(
                log.purpose_category, log.purpose_category)
            purpose_costs[label] = purpose_costs.get(label, 0) + log.cost_usd

        # ---- Department quota utilisation (always current month) ----
        dept_quotas = []
        for unit in request.env['openai.billing.org_unit'].sudo().search(
                [('state', '=', 'active')]):
            dept_quotas.append({
                'name': unit.name,
                'usage': unit.current_month_usage,
                'quota': unit.monthly_token_quota,
                'percentage': round(unit.usage_percentage * 100, 1),
            })

        return {
            'cost_by_department': {
                'labels': list(dept_costs.keys()),
                'data': [round(v, 2) for v in dept_costs.values()],
            },
            'usage_by_model': {
                'labels': list(model_usage.keys()),
                'data': list(model_usage.values()),
            },
            'cost_by_purpose': {
                'labels': list(purpose_costs.keys()),
                'data': [round(v, 2) for v in purpose_costs.values()],
            },
            'department_quotas': dept_quotas,
        }
