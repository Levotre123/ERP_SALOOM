from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCashExpenseAudit(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.btype = cls.env.ref("multi_activity_core.type_salon")
        cls.est = cls.env["multi.activity.establishment"].create(
            {
                "name": "Ops Site",
                "company_id": cls.env.company.id,
                "business_type_id": cls.btype.id,
            }
        )
        cls.category = cls.env.ref("multi_activity_operations.expense_cat_other")

    def test_cash_difference_minus_twenty(self):
        session = self.env["pos.session"].new(
            {
                "cash_register_balance_end": 500.0,
                "ma_counted_cash": 480.0,
            }
        )
        session._compute_ma_cash_difference()
        self.assertEqual(session.ma_expected_cash, 500.0)
        self.assertEqual(session.ma_difference, -20.0)

    def test_expense_confirm_and_no_delete(self):
        expense = self.env["multi.activity.expense"].create(
            {
                "establishment_id": self.est.id,
                "category_id": self.category.id,
                "amount": 25.0,
            }
        )
        expense.action_confirm()
        self.assertEqual(expense.state, "confirmed")
        audit = self.env["multi.activity.audit.log"].search(
            [("model", "=", "multi.activity.expense"), ("res_id", "=", expense.id)]
        )
        self.assertTrue(audit)
        with self.assertRaises(UserError):
            expense.unlink()

    def test_price_change_is_audited(self):
        product = self.env["product.template"].create(
            {
                "name": "Cut",
                "list_price": 10.0,
                "type": "service",
            }
        )
        product.list_price = 12.0
        audit = self.env["multi.activity.audit.log"].search(
            [
                ("action", "=", "price_change"),
                ("res_id", "=", product.id),
                ("old_value", "=", "10.0"),
                ("new_value", "=", "12.0"),
            ],
            limit=1,
        )
        self.assertTrue(audit)

    def test_low_stock_alert(self):
        product = self.env["product.product"].create(
            {
                "name": "Shampoo",
                "type": "consu",
                "is_storable": True,
                "ma_min_qty": 10.0,
                "list_price": 5.0,
            }
        )
        self.env["multi.activity.alert"]._cron_low_stock()
        alert = self.env["multi.activity.alert"].search(
            [("product_id", "=", product.id), ("state", "=", "open")], limit=1
        )
        self.assertTrue(alert)
        self.env["multi.activity.alert"]._cron_low_stock()
        self.assertEqual(
            self.env["multi.activity.alert"].search_count(
                [("product_id", "=", product.id), ("state", "=", "open")]
            ),
            1,
        )
