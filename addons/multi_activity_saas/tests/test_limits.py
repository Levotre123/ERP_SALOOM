from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSubscriptionLimits(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plan = cls.env.ref("multi_activity_saas.plan_basic")
        cls.btype = cls.env.ref("multi_activity_core.type_salon")
        cls.company = cls.env["res.company"].create({"name": "Basic Co"})
        cls.tenant = cls.env["multi.activity.tenant"].create(
            {
                "name": "Basic Tenant",
                "plan_id": cls.plan.id,
                "company_id": cls.company.id,
                "currency_id": cls.company.currency_id.id,
                "business_type_id": cls.btype.id,
                "state": "active",
            }
        )
        cls.company.tenant_id = cls.tenant.id

    def test_second_establishment_blocked_on_basic(self):
        if "multi.activity.entitlement" not in self.env:
            self.skipTest("Entitlement service is not installed")
        self.env["multi.activity.establishment"].create(
            {
                "name": "Only Site",
                "company_id": self.company.id,
                "business_type_id": self.btype.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.env["multi.activity.establishment"].create(
                {
                    "name": "Second Site",
                    "company_id": self.company.id,
                    "business_type_id": self.btype.id,
                }
            )
