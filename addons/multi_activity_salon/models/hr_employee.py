from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    ma_commission_percent = fields.Float(string="Commission %")
