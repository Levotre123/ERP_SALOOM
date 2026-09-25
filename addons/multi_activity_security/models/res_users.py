from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        entitlement = self.env["multi.activity.entitlement"]
        for user in records.filtered(lambda u: not u.share):
            entitlement.check_user_limit(user.company_id)
        return records
