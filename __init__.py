from . import models
from . import controllers


def _assign_admin_billing_group(env):
    """Post-init hook: add admin user to Billing Admin group."""
    group = env.ref('openai_billing.group_billing_admin', raise_if_not_found=False)
    admin = env.ref('base.user_admin', raise_if_not_found=False)
    if group and admin:
        admin.sudo().write({'groups_id': [(4, group.id)]})
