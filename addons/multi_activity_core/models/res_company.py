from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    establishment_ids = fields.One2many(
        "multi.activity.establishment",
        "company_id",
        string="Establishments",
    )
