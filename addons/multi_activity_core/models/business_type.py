from odoo import fields, models


class MultiActivityBusinessType(models.Model):
    _name = "multi.activity.business.type"
    _description = "Business Activity Type"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    industry_module = fields.Char(
        help="Technical name of the optional vertical addon (e.g. multi_activity_salon)."
    )
