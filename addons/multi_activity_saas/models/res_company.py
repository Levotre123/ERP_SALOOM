from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    tenant_id = fields.Many2one("multi.activity.tenant", ondelete="set null")
