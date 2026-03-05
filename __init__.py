from . import models
from . import controllers


def _assign_admin_billing_group(env):
    """Post-init hook: add admin user to all Billing groups."""
    admin = env.ref('base.user_admin', raise_if_not_found=False)
    if not admin:
        return
    group_refs = [
        'openai_billing.group_billing_user',
        'openai_billing.group_billing_manager',
        'openai_billing.group_billing_admin',
    ]
    for ref in group_refs:
        group = env.ref(ref, raise_if_not_found=False)
        if group:
            # Odoo 19 removed groups_id from res.users — write directly to the relation table
            env.cr.execute(
                "INSERT INTO res_groups_users_rel (gid, uid) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (group.id, admin.id),
            )
