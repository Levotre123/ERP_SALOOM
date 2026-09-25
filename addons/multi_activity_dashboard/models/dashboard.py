from datetime import timedelta

from odoo import api, fields, models


class MultiActivityDashboard(models.TransientModel):
    _name = "multi.activity.dashboard"
    _description = "Owner dashboard"

    period = fields.Selection(
        [
            ("today", "Today"),
            ("week", "This week"),
            ("month", "This month"),
            ("custom", "Custom"),
        ],
        default="today",
        required=True,
    )
    date_from = fields.Date()
    date_to = fields.Date()
    establishment_id = fields.Many2one("multi.activity.establishment")
    all_establishments = fields.Boolean(string="All establishments", default=False)
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
    )
    revenue = fields.Monetary(currency_field="currency_id")
    cash_received = fields.Monetary(currency_field="currency_id")
    expense_total = fields.Monetary(currency_field="currency_id")
    estimated_profit = fields.Monetary(currency_field="currency_id")
    previous_revenue = fields.Monetary(currency_field="currency_id")
    transaction_count = fields.Integer()
    low_stock_count = fields.Integer()
    cash_alert_count = fields.Integer()
    note = fields.Html(readonly=True)

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        values.setdefault("period", "today")
        values.setdefault("all_establishments", False)
        establishment = self.env.user.current_establishment_id
        if establishment and "establishment_id" in fields_list:
            values.setdefault("establishment_id", establishment.id)
        return values

    @api.onchange("period", "date_from", "date_to", "establishment_id", "all_establishments")
    def _onchange_filters(self):
        self._recompute_kpis()

    @api.model
    def action_open(self):
        dash = self.create(
            {
                "period": "today",
                "all_establishments": False,
                "establishment_id": self.env.user.current_establishment_id.id or False,
                "currency_id": self.env.company.currency_id.id,
            }
        )
        dash._recompute_kpis()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": dash.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_refresh(self):
        self.ensure_one()
        self._recompute_kpis()
        return {
            "type": "ir.actions.act_window",
            "res_model": "multi.activity.dashboard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    def _period_bounds(self, previous=False):
        today = fields.Date.context_today(self)
        if self.period == "today":
            start = today
            end = today
        elif self.period == "week":
            start = today - timedelta(days=today.weekday())
            end = today
        elif self.period == "month":
            start = today.replace(day=1)
            end = today
        else:
            start = self.date_from or today
            end = self.date_to or today
        if previous:
            span = (end - start).days + 1
            return start - timedelta(days=span), start - timedelta(days=1)
        return start, end

    def _cached_value(self, name, default=False):
        if name in self._cache:
            return self[name]
        return default

    def _establishment_ids(self):
        user = self.env.user
        allowed = user._ma_allowed_establishment_ids()
        all_establishments = self._cached_value("all_establishments", False)
        establishment = self._cached_value("establishment_id", self.env["multi.activity.establishment"])
        if all_establishments and (
            user.has_group("multi_activity_security.group_tenant_owner")
            or user.has_group("multi_activity_security.group_company_admin")
        ):
            return allowed
        if establishment and establishment in allowed:
            return establishment
        return allowed or self.env["multi.activity.establishment"]

    def _recompute_kpis(self):
        for dash in self:
            start, end = dash._period_bounds()
            prev_start, prev_end = dash._period_bounds(previous=True)
            dash.date_from = start
            dash.date_to = end
            dash.currency_id = dash.env.company.currency_id
            establishments = dash._establishment_ids()
            est_ids = establishments.ids
            order_domain = [
                ("company_id", "in", dash.env.companies.ids),
                ("state", "in", ["paid", "done", "invoiced"]),
                ("date_order", ">=", fields.Datetime.to_datetime(start)),
                ("date_order", "<", fields.Datetime.to_datetime(end) + timedelta(days=1)),
            ]
            if est_ids:
                order_domain.append(("establishment_id", "in", est_ids))
            grouped = dash.env["pos.order"].read_group(
                order_domain, ["amount_total"], [], lazy=False
            )
            revenue = grouped[0]["amount_total"] if grouped else 0.0
            count = grouped[0]["__count"] if grouped else 0
            cash_received = revenue
            if "pos.payment" in dash.env:
                Payment = dash.env["pos.payment"]
                pay_domain = []
                date_field = "payment_date" if "payment_date" in Payment._fields else False
                if date_field:
                    pay_domain += [(date_field, ">=", start), (date_field, "<=", end)]
                if "company_id" in Payment._fields:
                    pay_domain.append(("company_id", "in", dash.env.companies.ids))
                payments = Payment.search(pay_domain)
                if est_ids:
                    payments = payments.filtered(
                        lambda payment: not payment.pos_order_id.establishment_id
                        or payment.pos_order_id.establishment_id.id in est_ids
                    )
                cash_received = sum(payments.mapped("amount"))
            expense_domain = [
                ("company_id", "in", dash.env.companies.ids),
                ("state", "=", "confirmed"),
                ("date", ">=", start),
                ("date", "<=", end),
            ]
            if est_ids:
                expense_domain.append(("establishment_id", "in", est_ids))
            expenses = dash.env["multi.activity.expense"].read_group(
                expense_domain, ["amount"], [], lazy=False
            )
            expense_total = expenses[0]["amount"] if expenses else 0.0
            prev_domain = [
                ("company_id", "in", dash.env.companies.ids),
                ("state", "in", ["paid", "done", "invoiced"]),
                ("date_order", ">=", fields.Datetime.to_datetime(prev_start)),
                ("date_order", "<", fields.Datetime.to_datetime(prev_end) + timedelta(days=1)),
            ]
            if est_ids:
                prev_domain.append(("establishment_id", "in", est_ids))
            prev = dash.env["pos.order"].read_group(prev_domain, ["amount_total"], [], lazy=False)
            dash.revenue = revenue or 0.0
            dash.cash_received = cash_received or 0.0
            dash.expense_total = expense_total or 0.0
            dash.estimated_profit = (revenue or 0.0) - (expense_total or 0.0)
            dash.previous_revenue = prev[0]["amount_total"] if prev else 0.0
            dash.transaction_count = count or 0
            dash.low_stock_count = dash.env["multi.activity.alert"].search_count(
                [("alert_type", "in", ["low_stock", "out_of_stock"]), ("state", "=", "open")]
            )
            dash.cash_alert_count = dash.env["multi.activity.alert"].search_count(
                [("alert_type", "=", "cash_difference"), ("state", "=", "open")]
            )
            rows = dash.env["pos.order"].read_group(
                order_domain,
                ["amount_total"],
                ["establishment_id"],
                lazy=False,
            )
            lines = []
            for row in rows:
                name = row["establishment_id"][1] if row.get("establishment_id") else dash.env._("Unassigned")
                lines.append("<li>%s: %s</li>" % (name, row["amount_total"]))
            dash.note = dash.env._(
                "<p><b>Estimated profit</b> = Revenue (paid POS) − confirmed operational expenses. "
                "Cash received is POS payments in the period and is not the same as revenue.</p>"
                "<ul>%s</ul>"
            ) % "".join(lines)
