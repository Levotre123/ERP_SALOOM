from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    establishment_id = fields.Many2one(
        "multi.activity.establishment",
        ondelete="restrict",
        index=True,
    )
