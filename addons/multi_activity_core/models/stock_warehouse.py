from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    establishment_id = fields.Many2one(
        "multi.activity.establishment",
        ondelete="set null",
        index=True,
    )
