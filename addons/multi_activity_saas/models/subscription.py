from odoo import api, fields, models


class MultiActivitySubscription(models.Model):
    _name = "multi.activity.subscription"
    _description = "Tenant Subscription"
    _inherit = ["mail.thread"]
    _order = "id desc"

    name = fields.Char(required=True, copy=False, default="New")
    tenant_id = fields.Many2one("multi.activity.tenant", required=True, ondelete="cascade", index=True)
    plan_id = fields.Many2one("multi.activity.plan", required=True, ondelete="restrict")
    company_id = fields.Many2one(related="tenant_id.company_id", store=True, index=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("trial", "Trial"),
            ("active", "Active"),
            ("past_due", "Past Due"),
            ("grace", "Grace Period"),
            ("suspended", "Suspended"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    date_start = fields.Date(default=fields.Date.context_today)
    date_end = fields.Date()
    next_invoice_date = fields.Date()
    grace_days = fields.Integer(default=7)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("multi.activity.subscription") or "SUB"
        return super().create(vals_list)
