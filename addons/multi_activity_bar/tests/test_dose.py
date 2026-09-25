from odoo.tests import TransactionCase, tagged

from odoo.addons.multi_activity_bar.hooks import post_init_hook


@tagged("post_install", "-at_install")
class TestBarDose(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        post_init_hook(cls.env)

    def test_fifty_ml_from_750_bottle(self):
        dose = self.env.ref("multi_activity_bar.uom_dose", raise_if_not_found=False)
        bottle = self.env.ref("multi_activity_bar.uom_bottle_750", raise_if_not_found=False)
        ml = self.env.ref("multi_activity_bar.uom_ml", raise_if_not_found=False)
        if not (dose and bottle and ml):
            self.skipTest("Bar volume UoMs were not created")
        helper = self.env["multi.activity.bar.uom"]
        sold = helper.convert(1.0, dose, ml)
        self.assertAlmostEqual(sold, 50.0, places=4)
        bottle_ml = helper.convert(1.0, bottle, ml)
        self.assertAlmostEqual(bottle_ml, 750.0, places=3)
        remaining = bottle_ml - sold
        self.assertAlmostEqual(remaining, 700.0, places=3)
        remaining_ml = helper.convert(helper.convert(1.0, bottle, ml) - sold, ml, ml)
        self.assertAlmostEqual(remaining_ml, 700.0, places=2)
