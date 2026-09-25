from odoo import fields, models


class MultiActivityExpenseCategory(models.Model):
    _name = "multi.activity.expense.category"
    _description = "Expense Category"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    active = fields.Boolean(default=True)
