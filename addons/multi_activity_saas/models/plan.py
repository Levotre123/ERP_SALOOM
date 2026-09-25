from odoo import fields, models


class MultiActivityPlan(models.Model):
    _name = "multi.activity.plan"
    _description = "Subscription Plan"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    price = fields.Monetary(currency_field="currency_id")
    billing_period = fields.Selection(
        [("month", "Monthly"), ("year", "Yearly")],
        default="month",
        required=True,
    )
    max_establishments = fields.Integer(default=1)
    max_users = fields.Integer(default=3)
    trial_days = fields.Integer(default=14)
    feature_ids = fields.Many2many("multi.activity.feature", string="Features")
    description = fields.Text()
