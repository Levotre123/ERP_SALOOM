from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSalonAppointment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.btype = cls.env.ref("multi_activity_core.type_salon")
        cls.est = cls.env["multi.activity.establishment"].create(
            {
                "name": "Salon Test",
                "company_id": cls.env.company.id,
                "business_type_id": cls.btype.id,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Client"})
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Hairdresser", "ma_commission_percent": 30.0}
        )
        cls.service = cls.env["product.product"].create(
            {
                "name": "Haircut",
                "type": "service",
                "list_price": 20.0,
                "ma_duration": 0.5,
                "ma_commission_percent": 10.0,
            }
        )

    def test_commission_snapshot(self):
        appointment = self.env["salon.appointment"].create(
            {
                "establishment_id": self.est.id,
                "partner_id": self.partner.id,
                "employee_id": self.employee.id,
                "product_id": self.service.id,
                "start_datetime": "2026-09-25 10:00:00",
                "duration": 0.5,
                "price": 20.0,
            }
        )
        appointment.action_confirm()
        appointment.action_start()
        appointment.action_done()
        self.assertEqual(appointment.state, "done")
        self.assertEqual(appointment.commission_percent, 30.0)
        self.assertEqual(appointment.commission_amount, 6.0)
        self.employee.ma_commission_percent = 50.0
        self.assertEqual(appointment.commission_amount, 6.0)
