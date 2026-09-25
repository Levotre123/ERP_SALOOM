from odoo import api, fields, models


class MultiActivityTicket(models.Model):
    _name = "multi.activity.ticket"
    _description = "SaaS Support Ticket"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(required=True, default="New")
    tenant_id = fields.Many2one("multi.activity.tenant", required=True, index=True, ondelete="cascade")
    company_id = fields.Many2one(related="tenant_id.company_id", store=True, index=True)
    category = fields.Selection(
        [
            ("billing", "Billing"),
            ("technical", "Technical"),
            ("feature", "Feature"),
            ("other", "Other"),
        ],
        default="other",
        required=True,
    )
    priority = fields.Selection(
        [("0", "Low"), ("1", "Normal"), ("2", "High")],
        default="1",
        required=True,
    )
    description = fields.Text()
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")
    user_id = fields.Many2one("res.users", string="Assignee")
    state = fields.Selection(
        [
            ("new", "New"),
            ("in_progress", "In Progress"),
            ("resolved", "Resolved"),
            ("cancelled", "Cancelled"),
        ],
        default="new",
        required=True,
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("multi.activity.ticket") or "TCK"
        return super().create(vals_list)
