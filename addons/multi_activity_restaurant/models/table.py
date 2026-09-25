from odoo import fields, models


class RestaurantTable(models.Model):
    _name = "restaurant.table"
    _description = "Restaurant table"
    _inherit = ["multi.activity.establishment.mixin"]
    _order = "name"

    name = fields.Char(required=True)
    seats = fields.Integer(default=4)
    state = fields.Selection(
        [("free", "Free"), ("occupied", "Occupied")],
        default="free",
        required=True,
    )
    waiter_id = fields.Many2one("res.users")
    order_ids = fields.One2many("restaurant.order", "table_id")
