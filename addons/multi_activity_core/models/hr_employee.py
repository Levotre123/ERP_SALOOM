from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    establishment_ids = fields.Many2many(
        "multi.activity.establishment",
        "hr_employee_establishment_rel",
        "employee_id",
        "establishment_id",
        string="Establishments",
    )
