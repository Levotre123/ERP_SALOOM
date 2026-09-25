from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class MultiActivityTenant(models.Model):
    _name = "multi.activity.tenant"
    _description = "SaaS Tenant"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(copy=False, index=True)
    partner_id = fields.Many2one("res.partner", ondelete="restrict")
    owner_id = fields.Many2one("res.users", tracking=True)
    email = fields.Char()
    phone = fields.Char()
    country_id = fields.Many2one("res.country")
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    lang = fields.Selection(
        selection=lambda self: self.env["res.lang"].get_installed(),
        string="Language",
        default=lambda self: self.env.lang or "en_US",
        required=True,
        help="Default interface language for the owner and company partner.",
    )
    business_type_id = fields.Many2one("multi.activity.business.type")
    company_id = fields.Many2one("res.company", ondelete="restrict", index=True)
    plan_id = fields.Many2one("multi.activity.plan", required=True, tracking=True)
    subscription_id = fields.Many2one("multi.activity.subscription")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("trial", "Trial"),
            ("active", "Active"),
            ("past_due", "Past Due"),
            ("suspended", "Suspended"),
            ("expired", "Expired"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    date_registration = fields.Date(default=fields.Date.context_today)
    date_trial_end = fields.Date()
    domain = fields.Char()
    database_name = fields.Char(help="Reserved for future database-per-tenant provisioning.")
    provisioning_state = fields.Selection(
        [
            ("pending", "Pending"),
            ("done", "Done"),
            ("failed", "Failed"),
        ],
        default="pending",
        tracking=True,
    )
    provisioning_error = fields.Text()
    establishment_count = fields.Integer(compute="_compute_counts")
    user_count = fields.Integer(compute="_compute_counts")

    @api.depends("company_id")
    def _compute_counts(self):
        Establishment = self.env["multi.activity.establishment"]
        Users = self.env["res.users"]
        for tenant in self:
            if tenant.company_id:
                tenant.establishment_count = Establishment.search_count(
                    [("company_id", "=", tenant.company_id.id)]
                )
                tenant.user_count = Users.search_count(
                    [("company_ids", "in", tenant.company_id.id), ("share", "=", False)]
                )
            else:
                tenant.establishment_count = 0
                tenant.user_count = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("code"):
                vals["code"] = self.env["ir.sequence"].next_by_code("multi.activity.tenant") or "TNT"
        return super().create(vals_list)

    def action_provision(self):
        for tenant in self:
            tenant._provision()
        return True

    def _provision(self):
        self.ensure_one()
        log = self.env["multi.activity.provisioning.log"].create(
            {"tenant_id": self.id, "state": "running", "message": "Provisioning started"}
        )
        try:
            if self.company_id:
                company = self.company_id
            else:
                company = self.env["res.company"].sudo().create(
                    {
                        "name": self.name,
                        "currency_id": self.currency_id.id,
                        "email": self.email,
                        "phone": self.phone,
                        "country_id": self.country_id.id,
                    }
                )
                self.company_id = company.id
                company.tenant_id = self.id

            owner = self.owner_id
            if not owner:
                login = self.email or ("%s@tenant.local" % (self.code or "owner").lower())
                owner = self.env["res.users"].sudo().search([("login", "=", login)], limit=1)
                if not owner:
                    group_ids = [self.env.ref("base.group_user").id]
                    owner_group = self.env.ref(
                        "multi_activity_security.group_tenant_owner",
                        raise_if_not_found=False,
                    )
                    if owner_group:
                        group_ids.append(owner_group.id)
                    owner = self.env["res.users"].sudo().create(
                        {
                            "name": self.name,
                            "login": login,
                            "email": self.email or login,
                            "company_id": company.id,
                            "company_ids": [(6, 0, [company.id])],
                            "groups_id": [(6, 0, group_ids)],
                        }
                    )
                self.owner_id = owner.id

            owner.sudo().write(
                {
                    "company_id": company.id,
                    "company_ids": [(4, company.id)],
                    "lang": self.lang or owner.lang,
                }
            )
            if company.partner_id and self.lang:
                company.partner_id.sudo().write({"lang": self.lang})

            establishment = self.env["multi.activity.establishment"].sudo().search(
                [("company_id", "=", company.id)], limit=1
            )
            if not establishment:
                if not self.business_type_id:
                    raise UserError(self.env._("Set a business type before provisioning."))
                establishment = self.env["multi.activity.establishment"].sudo().create(
                    {
                        "name": self.name,
                        "company_id": company.id,
                        "business_type_id": self.business_type_id.id,
                        "manager_id": owner.id,
                        "user_ids": [(6, 0, [owner.id])],
                    }
                )
            owner.sudo().write(
                {
                    "establishment_ids": [(4, establishment.id)],
                    "current_establishment_id": establishment.id,
                    "default_establishment_id": establishment.id,
                }
            )
            self._detach_platform_users(company, owner)

            if not self.subscription_id:
                trial_end = fields.Date.context_today(self) + timedelta(days=self.plan_id.trial_days or 0)
                subscription = self.env["multi.activity.subscription"].sudo().create(
                    {
                        "tenant_id": self.id,
                        "plan_id": self.plan_id.id,
                        "state": "trial" if self.plan_id.trial_days else "active",
                        "date_end": trial_end if self.plan_id.trial_days else False,
                    }
                )
                self.subscription_id = subscription.id
                self.date_trial_end = trial_end if self.plan_id.trial_days else False
                self.state = "trial" if self.plan_id.trial_days else "active"

            self.provisioning_state = "done"
            self.provisioning_error = False
            log.write({"state": "done", "message": "Provisioning completed"})
        except Exception as exc:
            self.provisioning_state = "failed"
            self.provisioning_error = str(exc)
            log.write({"state": "failed", "message": str(exc)})
            raise

    def action_suspend(self):
        self.write({"state": "suspended"})
        if self.subscription_id:
            self.subscription_id.state = "suspended"

    def action_activate(self):
        self.write({"state": "active"})
        if self.subscription_id:
            self.subscription_id.state = "active"

    def action_cancel(self):
        self.write({"state": "cancelled"})
        if self.subscription_id:
            self.subscription_id.state = "cancelled"

    @api.model
    def _cron_expire_trials(self):
        today = fields.Date.context_today(self)
        expired = self.search(
            [("state", "=", "trial"), ("date_trial_end", "<", today)]
        )
        expired.write({"state": "past_due"})
        expired.mapped("subscription_id").write({"state": "past_due"})

    def _detach_platform_users(self, company, owner):
        users = self.env["res.users"].sudo().search(
            [("company_ids", "in", company.id), ("id", "!=", owner.id), ("share", "=", False)]
        )
        platform = self.env.ref(
            "multi_activity_security.group_platform_admin", raise_if_not_found=False
        )
        admin = self.env.ref("base.user_admin", raise_if_not_found=False)
        for user in users:
            keep = False
            if platform and user.has_group("multi_activity_security.group_platform_admin"):
                keep = True
            if admin and user.id == admin.id:
                keep = True
            if keep and len(user.company_ids) > 1:
                user.write({"company_ids": [(3, company.id)]})

    def has_feature(self, code):
        self.ensure_one()
        return bool(self.plan_id.feature_ids.filtered(lambda f: f.code == code))
