{
    'name': 'OpenAI Enterprise Billing & Token Management',
    'version': '19.0.1.0.0',
    'category': 'Administration',
    'summary': 'Granular department-level cost attribution and budget enforcement for OpenAI Enterprise API',
    'description': """
        OpenAI Enterprise API Billing and Token Management System
        ==========================================================

        Gap Analysis Enhancement: Departmental cost attribution
        and real-time budget threshold enforcement.

        Features:
        - Organisational Unit management with monthly token quotas
        - Real-time usage monitoring dashboard (Chart.js)
        - Automated budget threshold alerts (80 / 90 / 100 percent)
        - Automatic API access suspension at hard limits
        - Project-based cost tagging
        - Monthly expenditure reports (CSV and PDF)
        - Immutable administrative audit trail
        - Model-level access controls per department
        - Departmental self-service read-only portal
    """,
    'author': 'Afsah',
    'depends': ['base', 'web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/grid_intensity_data.xml',
        'data/default_models.xml',
        'data/cron_data.xml',
        'views/dashboard_action.xml',
        'views/menu.xml',
        'views/ai_model_views.xml',
        'views/grid_intensity_views.xml',
        'views/org_unit_views.xml',
        'views/api_key_views.xml',
        'views/usage_log_views.xml',
        'views/project_tag_views.xml',
        'views/quota_alert_views.xml',
        'views/audit_trail_views.xml',
        'views/report_views.xml',
        'report/monthly_report.xml',
        'data/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'openai_billing/static/src/css/billing_dashboard.css',
            'openai_billing/static/src/js/billing_dashboard.js',
            'openai_billing/static/src/xml/billing_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'post_init_hook': '_assign_admin_billing_group',
}
