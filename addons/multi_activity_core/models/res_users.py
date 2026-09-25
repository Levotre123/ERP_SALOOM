from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    establishment_ids = fields.Many2many(
        "multi.activity.establishment",
        "res_users_establishment_rel",
        "user_id",
        "establishment_id",
        string="Allowed Establishments",
    )
    default_establishment_id = fields.Many2one(
        "multi.activity.establishment",
        domain="[('id', 'in', establishment_ids)]",
    )
    current_establishment_id = fields.Many2one(
        "multi.activity.establishment",
        domain="[('id', 'in', establishment_ids)]",
    )

    def action_switch_establishment(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Switch Establishment"),
            "res_model": "multi.activity.switch.establishment",
            "view_mode": "form",
            "target": "new",
        }

    def _ma_allowed_establishment_ids(self):
        self.ensure_one()
        if self.has_group("multi_activity_security.group_tenant_owner") or self.has_group(
            "multi_activity_security.group_company_admin"
        ):
            return self.env["multi.activity.establishment"].sudo().search(
                [("company_id", "in", self.company_ids.ids)]
            )
        return self.establishment_ids
