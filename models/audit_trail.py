from odoo import models, fields
from odoo.exceptions import UserError


class AuditTrail(models.Model):
    _name = 'openai.billing.audit_trail'
    _description = 'Administrative Audit Trail'
    _order = 'create_date desc'

    action_type = fields.Selection([
        ('quota_change', 'Quota Modification'),
        ('role_change', 'Role Assignment Change'),
        ('suspension', 'Service Suspension'),
        ('override', 'Quota Override / Reactivation'),
        ('deletion', 'Data Deletion'),
        ('key_change', 'API Key Change'),
        ('model_access', 'Model Access Change'),
    ], string='Action Type', required=True)
    org_unit_id = fields.Many2one(
        'openai.billing.org_unit', string='Department')
    performed_by = fields.Many2one(
        'res.users', string='Performed By', required=True,
        default=lambda self: self.env.uid)
    old_value = fields.Char(string='Previous Value')
    new_value = fields.Char(string='New Value')
    description = fields.Text(string='Description', required=True)

    # ------------------------------------------------------------------
    # Immutability enforcement  (FR-17)
    # ------------------------------------------------------------------
    def unlink(self):
        if not self.env.context.get('force_delete'):
            raise UserError(
                'Audit trail records cannot be deleted. '
                'They are permanent and immutable.')
        return super().unlink()
