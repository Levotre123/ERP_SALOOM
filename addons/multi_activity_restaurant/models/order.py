from odoo import api, fields, models
from odoo.exceptions import UserError


class RestaurantOrder(models.Model):
    _name = "restaurant.order"
    _description = "Restaurant order"
    _inherit = ["multi.activity.establishment.mixin", "mail.thread"]
    _order = "id desc"

    name = fields.Char(required=True, copy=False, default="New")
    table_id = fields.Many2one("restaurant.table", required=True, tracking=True)
    waiter_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    pos_order_id = fields.Many2one("pos.order")
    state = fields.Selection(
        [
            ("new", "New"),
            ("preparation", "In preparation"),
            ("ready", "Ready"),
            ("served", "Served"),
            ("paid", "Paid"),
            ("cancelled", "Cancelled"),
        ],
        default="new",
        required=True,
        tracking=True,
    )
    note = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("restaurant.order") or "RSO"
        records = super().create(vals_list)
        records.mapped("table_id").write({"state": "occupied"})
        return records

    def action_send_kitchen(self):
        self.write({"state": "preparation"})

    def action_ready(self):
        self.write({"state": "ready"})

    def action_served(self):
        self.write({"state": "served"})

    def action_paid(self):
        self.write({"state": "paid"})
        for order in self:
            if not order.table_id.order_ids.filtered(lambda o: o.state not in ("paid", "cancelled") and o != order):
                order.table_id.state = "free"

    def action_cancel(self):
        if not (
            self.env.user.has_group("multi_activity_security.group_manager")
            or self.env.user.has_group("multi_activity_security.group_tenant_owner")
        ):
            raise UserError(self.env._("You are not allowed to cancel this order."))
        self.write({"state": "cancelled"})
        self.env["multi.activity.audit.log"]._log_records(
            self, "restaurant_cancel", source="restaurant"
        )
        for order in self:
            open_orders = order.table_id.order_ids.filtered(
                lambda other: other.state not in ("paid", "cancelled")
            )
            if not open_orders:
                order.table_id.state = "free"
