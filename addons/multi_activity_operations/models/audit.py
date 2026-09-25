from odoo import api, fields, models


class MultiActivityAuditLog(models.Model):
    _name = "multi.activity.audit.log"
    _description = "Sensitive operation audit"
    _order = "id desc"

    name = fields.Char(required=True, copy=False, default="New")
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user, required=True, index=True)
    timestamp = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    company_id = fields.Many2one("res.company", index=True, default=lambda self: self.env.company)
    tenant_id = fields.Many2one("multi.activity.tenant", index=True)
    establishment_id = fields.Many2one("multi.activity.establishment", index=True)
    model = fields.Char(index=True)
    res_id = fields.Integer(index=True)
    action = fields.Char(required=True, index=True)
    old_value = fields.Text()
    new_value = fields.Text()
    reason = fields.Char()
    source = fields.Char()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("multi.activity.audit") or "AUD"
            if not vals.get("tenant_id") and vals.get("company_id"):
                company = self.env["res.company"].browse(vals["company_id"])
                vals["tenant_id"] = company.tenant_id.id
        return super().create(vals_list)

    @api.model
    def log_event(self, action, record=None, old_value=None, new_value=None, reason=None, source="ui"):
        vals = {
            "action": action,
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason,
            "source": source,
            "company_id": self.env.company.id,
        }
        if record:
            vals.update(
                {
                    "model": record._name,
                    "res_id": record.id,
                    "company_id": getattr(record, "company_id", self.env.company).id
                    if "company_id" in record._fields
                    else self.env.company.id,
                    "establishment_id": record.establishment_id.id
                    if "establishment_id" in record._fields and record.establishment_id
                    else False,
                }
            )
        return self.create(vals)

    @api.model
    def _log_records(self, records, action, reason=None, source="ui", old_value=None, new_value=None):
        for record in records:
            self.log_event(
                action,
                record=record,
                reason=reason,
                source=source,
                old_value=old_value,
                new_value=new_value,
            )
