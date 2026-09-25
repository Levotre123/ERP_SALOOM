from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class SalonAppointment(models.Model):
    _name = "salon.appointment"
    _description = "Salon appointment"
    _inherit = ["multi.activity.establishment.mixin", "mail.thread", "mail.activity.mixin"]
    _order = "start_datetime desc"

    name = fields.Char(required=True, copy=False, default="New")
    partner_id = fields.Many2one("res.partner", required=True, tracking=True)
    employee_id = fields.Many2one("hr.employee", required=True, tracking=True)
    product_id = fields.Many2one(
        "product.product",
        required=True,
        domain="[('type', '=', 'service')]",
        tracking=True,
    )
    start_datetime = fields.Datetime(required=True, index=True)
    end_datetime = fields.Datetime()
    duration = fields.Float(string="Duration (hours)")
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    price = fields.Monetary(currency_field="currency_id")
    commission_percent = fields.Float(readonly=True)
    commission_amount = fields.Monetary(currency_field="currency_id", readonly=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("in_progress", "In progress"),
            ("done", "Completed"),
            ("cancelled", "Cancelled"),
            ("no_show", "No show"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("salon.appointment") or "APT"
        records = super().create(vals_list)
        for appointment in records:
            company = appointment.company_id or self.env.company
            self.env["multi.activity.entitlement"].check_feature(company, "industry_salon")
            self.env["multi.activity.entitlement"].check_operational(company)
        return records

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.price = self.product_id.list_price
            self.duration = self.product_id.ma_duration
            if self.start_datetime and self.duration:
                self.end_datetime = self.start_datetime + timedelta(hours=self.duration)

    @api.onchange("start_datetime", "duration")
    def _onchange_start_duration(self):
        if self.start_datetime and self.duration:
            self.end_datetime = self.start_datetime + timedelta(hours=self.duration)

    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_start(self):
        self.write({"state": "in_progress"})

    def action_done(self):
        for appointment in self:
            percent = (
                appointment.employee_id.ma_commission_percent
                or appointment.product_id.product_tmpl_id.ma_commission_percent
            )
            amount = appointment.price * percent / 100.0
            appointment.write(
                {
                    "state": "done",
                    "commission_percent": percent,
                    "commission_amount": amount,
                }
            )
        self.env["multi.activity.audit.log"]._log_records(
            self, "appointment_done", source="salon"
        )

    def action_cancel(self):
        self.write({"state": "cancelled"})
        self.env["multi.activity.audit.log"]._log_records(
            self, "appointment_cancel", source="salon"
        )

    def action_no_show(self):
        self.write({"state": "no_show"})

    def unlink(self):
        raise UserError(self.env._("Appointments cannot be deleted. Cancel them instead."))
