from odoo import api, fields, models


class PosSession(models.Model):
    _inherit = "pos.session"

    establishment_id = fields.Many2one(
        related="config_id.establishment_id",
        store=True,
        index=True,
    )
    ma_counted_cash = fields.Monetary(currency_field="currency_id")
    ma_expected_cash = fields.Monetary(
        compute="_compute_ma_cash_difference",
        store=True,
        currency_field="currency_id",
    )
    ma_difference = fields.Monetary(
        compute="_compute_ma_cash_difference",
        store=True,
        currency_field="currency_id",
    )

    @api.depends(
        "cash_register_balance_end",
        "cash_register_balance_end_real",
        "ma_counted_cash",
        "cash_register_balance_start",
    )
    def _compute_ma_cash_difference(self):
        for session in self:
            expected = session.cash_register_balance_end
            counted = session.ma_counted_cash
            if not counted and session.cash_register_balance_end_real:
                counted = session.cash_register_balance_end_real
            session.ma_expected_cash = expected
            session.ma_difference = counted - expected if counted or expected else 0.0

    def write(self, vals):
        closed = self.filtered(lambda s: s.state != "closed")
        result = super().write(vals)
        if vals.get("state") == "closed":
            (closed & self)._ma_on_cash_closed()
        return result

    def _ma_on_cash_closed(self):
        Audit = self.env["multi.activity.audit.log"]
        Alert = self.env["multi.activity.alert"]
        for session in self:
            Audit.log_event(
                "cash_close",
                record=session,
                old_value=str(session.ma_expected_cash),
                new_value=str(session.ma_counted_cash or session.cash_register_balance_end_real),
                reason="Cash session closed",
                source="pos",
            )
            tolerance = session.config_id.ma_cash_tolerance or 0.0
            difference = session.ma_difference
            if abs(difference) > tolerance:
                Alert.create(
                    {
                        "name": "Cash difference %s on %s" % (difference, session.name),
                        "alert_type": "cash_difference",
                        "session_id": session.id,
                        "establishment_id": session.establishment_id.id,
                        "company_id": session.company_id.id,
                        "note": "Expected %s / counted %s / difference %s"
                        % (session.ma_expected_cash, session.ma_counted_cash, difference),
                    }
                )
