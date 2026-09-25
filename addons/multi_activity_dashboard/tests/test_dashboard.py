from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDashboardOpen(TransactionCase):
    def test_action_open_does_not_recurse(self):
        action = self.env["multi.activity.dashboard"].action_open()
        self.assertEqual(action["res_model"], "multi.activity.dashboard")
        self.assertTrue(action.get("res_id"))
        dash = self.env["multi.activity.dashboard"].browse(action["res_id"])
        self.assertEqual(dash.period, "today")
        self.assertFalse(dash.all_establishments)
