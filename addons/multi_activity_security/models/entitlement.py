from odoo import models
from odoo.exceptions import UserError, ValidationError


class MultiActivityEntitlement(models.AbstractModel):
    _name = "multi.activity.entitlement"
    _description = "Subscription entitlement checks"

    def _tenant_for_company(self, company):
        if not company:
            return self.env["multi.activity.tenant"]
        if company.tenant_id:
            return company.tenant_id
        return self.env["multi.activity.tenant"].sudo().search(
            [("company_id", "=", company.id)], limit=1
        )

    def check_establishment_limit(self, company):
        tenant = self._tenant_for_company(company)
        if not tenant or not tenant.plan_id:
            return
        plan = tenant.plan_id
        count = self.env["multi.activity.establishment"].sudo().search_count(
            [("company_id", "=", company.id)]
        )
        if count > plan.max_establishments:
            raise ValidationError(
                self.env._(
                    "Plan %(plan)s allows %(max)s establishment(s). Limit reached.",
                    plan=plan.name,
                    max=plan.max_establishments,
                )
            )

    def check_user_limit(self, company):
        tenant = self._tenant_for_company(company)
        if not tenant or not tenant.plan_id:
            return
        plan = tenant.plan_id
        count = self.env["res.users"].sudo().search_count(
            [("company_ids", "in", company.id), ("share", "=", False)]
        )
        if count > plan.max_users:
            raise ValidationError(
                self.env._(
                    "Plan %(plan)s allows %(max)s user(s). Limit reached.",
                    plan=plan.name,
                    max=plan.max_users,
                )
            )

    def check_feature(self, company, code):
        tenant = self._tenant_for_company(company)
        if tenant and not tenant.has_feature(code):
            raise UserError(
                self.env._("Feature %(code)s is not included in the current plan.", code=code)
            )
        return True

    def check_operational(self, company):
        tenant = self._tenant_for_company(company)
        if tenant and tenant.state in ("suspended", "cancelled", "expired"):
            raise UserError(self.env._("This subscription is not active."))
