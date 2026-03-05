import csv
import io

from odoo import http
from odoo.http import request, content_disposition


class OpenAIBillingExport(http.Controller):
    """CSV / PDF export endpoints (FR-12)."""

    @http.route('/openai_billing/export/csv',
                type='http', auth='user')
    def export_csv(self, report_id=None, **kwargs):
        report = request.env['openai.billing.report'].browse(int(report_id))
        if not report.exists():
            return request.not_found()

        logs = report._get_usage_logs()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Timestamp', 'Department', 'User', 'API Key', 'Model',
            'Project', 'Purpose', 'Prompt Tokens', 'Completion Tokens',
            'Total Tokens', 'Cost (USD)',
        ])

        for log in logs:
            writer.writerow([
                (log.request_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                 if log.request_timestamp else ''),
                log.org_unit_id.name or '',
                log.user_id.name or '',
                log.api_key_id.name or '',
                log.ai_model_id.name or '',
                log.project_tag_id.name or '',
                log.purpose_category or '',
                log.prompt_tokens,
                log.completion_tokens,
                log.total_tokens,
                f'{log.cost_usd:.6f}',
            ])

        content = output.getvalue()
        filename = (
            f"openai_billing_{report.period_start}_{report.period_end}.csv")

        return request.make_response(
            content,
            headers=[
                ('Content-Type', 'text/csv; charset=utf-8'),
                ('Content-Disposition', content_disposition(filename)),
            ],
        )
