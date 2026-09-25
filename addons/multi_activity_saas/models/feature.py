from odoo import fields, models


class MultiActivityFeature(models.Model):
    _name = "multi.activity.feature"
    _description = "SaaS Feature"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, index=True)
    category = fields.Selection(
        [
            ("core", "Core"),
            ("stock", "Stock"),
            ("report", "Reporting"),
            ("industry", "Industry"),
            ("premium", "Premium"),
        ],
        default="core",
        required=True,
    )
    description = fields.Text()
    active = fields.Boolean(default=True)
