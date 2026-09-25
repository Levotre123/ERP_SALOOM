from odoo import fields, models
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = "pos.order"

    establishment_id = fields.Many2one(
        related="config_id.establishment_id",
        store=True,
        index=True,
    )

    def refund(self):
        self.env["multi.activity.audit.log"]._log_records(
            self, "refund", source="pos", reason="POS refund"
        )
        return super().refund()

    def write(self, vals):
        if vals.get("state") == "cancel":
            paid = self.filtered(lambda order: order.state in ("paid", "done", "invoiced"))
            if paid and not (
                self.env.user.has_group("multi_activity_security.group_manager")
                or self.env.user.has_group("multi_activity_security.group_tenant_owner")
                or self.env.user.has_group("multi_activity_security.group_company_admin")
                or self.env.user.has_group("point_of_sale.group_pos_manager")
            ):
                raise UserError(self.env._("You are not allowed to cancel this sale."))
            if paid:
                self.env["multi.activity.audit.log"]._log_records(
                    paid, "cancel", source="pos", reason="POS cancellation"
                )
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda order: order.state not in ("draft", "cancel")):
            raise UserError(
                self.env._("Paid sales cannot be deleted. Cancel or refund them to keep the history.")
            )
        return super().unlink()
