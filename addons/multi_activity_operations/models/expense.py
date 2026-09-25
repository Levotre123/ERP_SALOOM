from odoo import api, fields, models
from odoo.exceptions import UserError


class MultiActivityExpense(models.Model):
    _name = "multi.activity.expense"
    _description = "Operational Expense"
    _inherit = ["multi.activity.establishment.mixin", "mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(required=True, copy=False, default="New")
    category_id = fields.Many2one(
        "multi.activity.expense.category",
        required=True,
        ondelete="restrict",
    )
    date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )
    amount = fields.Monetary(currency_field="currency_id", required=True)
    user_id = fields.Many2one(
        "res.users",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    note = fields.Text()
    attachment_ids = fields.Many2many("ir.attachment", string="Receipts")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("multi.activity.expense") or "EXP"
        records = super().create(vals_list)
        self.env["multi.activity.audit.log"]._log_records(
            records, "create", source="expense"
        )
        return records

    def action_confirm(self):
        for expense in self:
            if expense.state != "draft":
                raise UserError(self.env._("Only draft expenses can be confirmed."))
            expense.state = "confirmed"
        self.env["multi.activity.audit.log"]._log_records(
            self, "confirm", source="expense"
        )

    def action_cancel(self):
        for expense in self:
            if expense.state == "cancelled":
                continue
            expense.state = "cancelled"
        self.env["multi.activity.audit.log"]._log_records(
            self, "cancel", source="expense", reason="Expense cancelled"
        )

    def unlink(self):
        raise UserError(
            self.env._("Expenses cannot be deleted. Cancel them to keep the financial history.")
        )
