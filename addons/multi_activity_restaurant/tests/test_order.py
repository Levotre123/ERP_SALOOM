from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRestaurantOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.btype = cls.env.ref("multi_activity_core.type_restaurant")
        cls.est = cls.env["multi.activity.establishment"].create(
            {
                "name": "Restaurant Test",
                "company_id": cls.env.company.id,
                "business_type_id": cls.btype.id,
            }
        )
        cls.table = cls.env["restaurant.table"].create(
            {
                "name": "Table 4",
                "establishment_id": cls.est.id,
            }
        )

    def test_table_order_kitchen_flow(self):
        order = self.env["restaurant.order"].create(
            {
                "table_id": self.table.id,
                "establishment_id": self.est.id,
            }
        )
        self.assertEqual(self.table.state, "occupied")
        order.action_send_kitchen()
        self.assertEqual(order.state, "preparation")
        order.action_ready()
        order.action_served()
        order.action_paid()
        self.assertEqual(order.state, "paid")
        self.assertEqual(self.table.state, "free")
