from odoo import models
from odoo.exceptions import AccessDenied


class ResUsers(models.Model):
    _inherit = "res.users"

    def _check_credentials(self, credential, env):
        result = super()._check_credentials(credential, env)
        platform = self.env.ref(
            "multi_activity_security.group_platform_admin", raise_if_not_found=False
        )
        if platform and self.has_group("multi_activity_security.group_platform_admin"):
            return result
        tenant = self.env["multi.activity.tenant"].sudo().search(
            [("company_id", "=", self.company_id.id), ("state", "=", "suspended")],
            limit=1,
        )
        if tenant:
            raise AccessDenied(self.env._("This subscription is suspended."))
        return result
