from odoo import models


class MultiActivityBarUom(models.AbstractModel):
    _name = "multi.activity.bar.uom"
    _description = "Bar UoM conversion helpers"

    def convert(self, qty, from_uom, to_uom):
        """Convert using Odoo UoM rounding, never raw floats."""
        return from_uom._compute_quantity(qty, to_uom, round=True)
