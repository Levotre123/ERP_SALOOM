from odoo import api, fields, models
from odoo.addons.base.models.res_partner import _tz_get


class MultiActivityEstablishment(models.Model):
    _name = "multi.activity.establishment"
    _description = "Establishment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(copy=False, index=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        ondelete="restrict",
    )
    business_type_id = fields.Many2one(
        "multi.activity.business.type",
        required=True,
        tracking=True,
        ondelete="restrict",
    )
    street = fields.Char()
    street2 = fields.Char()
    city = fields.Char()
    zip = fields.Char()
    country_id = fields.Many2one("res.country")
    phone = fields.Char()
    email = fields.Char()
    tz = fields.Selection(
        selection=_tz_get,
        string="Timezone",
        default=lambda self: self.env.user.tz or "UTC",
    )
    manager_id = fields.Many2one("res.users", tracking=True)
    warehouse_id = fields.Many2one("stock.warehouse", tracking=True)
    pos_config_id = fields.Many2one("pos.config", tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    user_ids = fields.Many2many(
        "res.users",
        "res_users_establishment_rel",
        "establishment_id",
        "user_id",
        string="Authorized Users",
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("code"):
                vals["code"] = self.env["ir.sequence"].next_by_code("multi.activity.establishment") or "/"
        records = super().create(vals_list)
        records._ensure_warehouse()
        return records

    def _ensure_warehouse(self):
        Warehouse = self.env["stock.warehouse"].sudo()
        for establishment in self:
            if establishment.warehouse_id:
                continue
            warehouse = Warehouse.search(
                [("establishment_id", "=", establishment.id)], limit=1
            )
            if not warehouse:
                warehouse = Warehouse.create(
                    {
                        "name": establishment.name,
                        "code": ("E%s" % establishment.id)[:5],
                        "company_id": establishment.company_id.id,
                        "establishment_id": establishment.id,
                    }
                )
            establishment.warehouse_id = warehouse.id

    @api.constrains("company_id")
    def _check_plan_establishment_limit(self):
        if "multi.activity.entitlement" not in self.env:
            return
        entitlement = self.env["multi.activity.entitlement"]
        for establishment in self:
            entitlement.check_establishment_limit(establishment.company_id)
