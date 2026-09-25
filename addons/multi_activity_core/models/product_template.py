from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    ma_duration = fields.Float(string="Service Duration (hours)")
    ma_commission_percent = fields.Float(string="Default Commission %")
    ma_business_type_id = fields.Many2one("multi.activity.business.type")
    ma_min_qty = fields.Float(string="Low Stock Threshold")
