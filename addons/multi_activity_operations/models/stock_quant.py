from odoo import api, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def action_apply_inventory(self):
        Audit = self.env["multi.activity.audit.log"]
        for quant in self:
            Audit.log_event(
                "inventory_adjustment",
                record=quant,
                old_value=str(quant.quantity),
                new_value=str(quant.inventory_quantity),
                reason="Inventory count applied",
                source="stock",
            )
        return super().action_apply_inventory()

    @api.model
    def _get_available_qty(self, product):
        quants = self.search([("product_id", "=", product.id), ("location_id.usage", "=", "internal")])
        return sum(quants.mapped("quantity")) - sum(quants.mapped("reserved_quantity"))
