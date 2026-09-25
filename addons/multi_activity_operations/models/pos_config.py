from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    ma_cash_tolerance = fields.Monetary(
        string="Cash difference tolerance",
        currency_field="currency_id",
    )
