from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    ma_is_drink = fields.Boolean(string="Bar drink")
    ma_dose_uom_id = fields.Many2one("uom.uom", string="Dose UoM")
    ma_bottle_uom_id = fields.Many2one("uom.uom", string="Bottle UoM")
