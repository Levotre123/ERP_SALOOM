from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def write(self, vals):
        price_changed = "list_price" in vals
        old_prices = {rec.id: rec.list_price for rec in self} if price_changed else {}
        result = super().write(vals)
        if price_changed:
            Audit = self.env["multi.activity.audit.log"]
            for product in self:
                if old_prices.get(product.id) != product.list_price:
                    Audit.log_event(
                        "price_change",
                        record=product,
                        old_value=str(old_prices.get(product.id)),
                        new_value=str(product.list_price),
                        source="product",
                    )
        return result
