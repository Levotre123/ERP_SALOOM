from odoo import api, fields, models


class MultiActivityAlert(models.Model):
    _name = "multi.activity.alert"
    _description = "Operational alert"
    _order = "id desc"
    _inherit = ["mail.thread"]

    name = fields.Char(required=True)
    alert_type = fields.Selection(
        [
            ("low_stock", "Low stock"),
            ("out_of_stock", "Out of stock"),
            ("cash_difference", "Cash difference"),
            ("large_expense", "Large expense"),
            ("sensitive", "Sensitive operation"),
            ("inactivity", "Establishment inactivity"),
        ],
        required=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    establishment_id = fields.Many2one("multi.activity.establishment", index=True)
    product_id = fields.Many2one("product.product")
    session_id = fields.Many2one("pos.session")
    state = fields.Selection(
        [("open", "Open"), ("done", "Done")],
        default="open",
        required=True,
        tracking=True,
    )
    note = fields.Text()

    def action_done(self):
        self.write({"state": "done"})

    @api.model
    def _cron_low_stock(self):
        domain = [("ma_min_qty", ">", 0)]
        if "is_storable" in self.env["product.product"]._fields:
            domain.append(("is_storable", "=", True))
        else:
            domain.append(("type", "!=", "service"))
        products = self.env["product.product"].search(domain)
        Quant = self.env["stock.quant"]
        Alert = self.env["multi.activity.alert"]
        for product in products:
            qty = Quant._get_available_qty(product)
            if qty > product.ma_min_qty:
                continue
            alert_type = "out_of_stock" if qty <= 0 else "low_stock"
            existing = Alert.search(
                [
                    ("product_id", "=", product.id),
                    ("alert_type", "=", alert_type),
                    ("state", "=", "open"),
                ],
                limit=1,
            )
            if existing:
                continue
            Alert.create(
                {
                    "name": "%s: %s (qty %s)" % (alert_type, product.display_name, qty),
                    "alert_type": alert_type,
                    "product_id": product.id,
                    "company_id": product.company_id.id or self.env.company.id,
                    "note": "Available %s / minimum %s" % (qty, product.ma_min_qty),
                }
            )
