from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestTenantIsolation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plan = cls.env.ref("multi_activity_saas.plan_pro")
        cls.btype = cls.env.ref("multi_activity_core.type_salon")
        cls.company_a = cls.env["res.company"].create({"name": "Tenant A Co"})
        cls.company_b = cls.env["res.company"].create({"name": "Tenant B Co"})
        cls.tenant_a = cls.env["multi.activity.tenant"].create(
            {
                "name": "Tenant A",
                "plan_id": cls.plan.id,
                "company_id": cls.company_a.id,
                "currency_id": cls.company_a.currency_id.id,
                "business_type_id": cls.btype.id,
                "state": "active",
            }
        )
        cls.tenant_b = cls.env["multi.activity.tenant"].create(
            {
                "name": "Tenant B",
                "plan_id": cls.plan.id,
                "company_id": cls.company_b.id,
                "currency_id": cls.company_b.currency_id.id,
                "business_type_id": cls.btype.id,
                "state": "active",
            }
        )
        cls.company_a.tenant_id = cls.tenant_a.id
        cls.company_b.tenant_id = cls.tenant_b.id
        cls.est_a = cls.env["multi.activity.establishment"].create(
            {
                "name": "Salon A",
                "company_id": cls.company_a.id,
                "business_type_id": cls.btype.id,
            }
        )
        cls.est_b = cls.env["multi.activity.establishment"].create(
            {
                "name": "Salon B",
                "company_id": cls.company_b.id,
                "business_type_id": cls.btype.id,
            }
        )
        cls.user_a = new_test_user(
            cls.env,
            login="owner_a",
            groups="multi_activity_security.group_tenant_owner",
            company_id=cls.company_a.id,
        )
        cls.user_b = new_test_user(
            cls.env,
            login="owner_b",
            groups="multi_activity_security.group_tenant_owner",
            company_id=cls.company_b.id,
        )
        cls.user_a.company_ids = cls.company_a
        cls.user_b.company_ids = cls.company_b
        cls.user_a.establishment_ids = cls.est_a
        cls.user_b.establishment_ids = cls.est_b
        cls.est_a.user_ids = cls.user_a
        cls.est_b.user_ids = cls.user_b
        category = cls.env.ref("multi_activity_operations.expense_cat_other")
        cls.expense_b = cls.env["multi.activity.expense"].create(
            {
                "establishment_id": cls.est_b.id,
                "category_id": category.id,
                "amount": 40.0,
                "user_id": cls.user_b.id,
            }
        )
        cls.partner_b = cls.env["res.partner"].create(
            {"name": "Customer B", "company_id": cls.company_b.id}
        )

    def test_user_a_cannot_search_tenant_b_expense(self):
        Expense = self.env["multi.activity.expense"].with_user(self.user_a)
        self.assertFalse(Expense.search([("id", "=", self.expense_b.id)]))
        with self.assertRaises(AccessError):
            self.expense_b.with_user(self.user_a).read(["name"])

    def test_user_a_cannot_read_tenant_b_establishment(self):
        Establishment = self.env["multi.activity.establishment"].with_user(self.user_a)
        self.assertFalse(Establishment.search([("id", "=", self.est_b.id)]))
        with self.assertRaises(AccessError):
            self.est_b.with_user(self.user_a).read(["name"])

    def test_user_a_cannot_read_tenant_b_partner(self):
        Partner = self.env["res.partner"].with_user(self.user_a)
        self.assertFalse(Partner.search([("id", "=", self.partner_b.id)]))

    def test_user_a_cannot_read_tenant_b_appointment(self):
        if "salon.appointment" not in self.env:
            self.skipTest("Salon is not installed")
        employee = self.env["hr.employee"].create(
            {"name": "Barber B", "company_id": self.company_b.id}
        )
        service = self.env["product.product"].create(
            {"name": "Fade", "type": "service", "list_price": 15.0, "company_id": self.company_b.id}
        )
        appointment = self.env["salon.appointment"].create(
            {
                "establishment_id": self.est_b.id,
                "partner_id": self.partner_b.id,
                "employee_id": employee.id,
                "product_id": service.id,
                "start_datetime": "2026-09-25 11:00:00",
                "price": 15.0,
            }
        )
        Appointment = self.env["salon.appointment"].with_user(self.user_a)
        self.assertFalse(Appointment.search([("id", "=", appointment.id)]))
        with self.assertRaises(AccessError):
            appointment.with_user(self.user_a).read(["name"])

    def test_user_a_cannot_read_tenant_b_ticket(self):
        ticket = self.env["multi.activity.ticket"].create(
            {
                "tenant_id": self.tenant_b.id,
                "description": "Secret",
            }
        )
        Ticket = self.env["multi.activity.ticket"].with_user(self.user_a)
        self.assertFalse(Ticket.search([("id", "=", ticket.id)]))


@tagged("post_install", "-at_install")
class TestEstablishmentIsolation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plan = cls.env.ref("multi_activity_saas.plan_business")
        cls.btype = cls.env.ref("multi_activity_core.type_salon")
        cls.company = cls.env["res.company"].create({"name": "Multi Est Co"})
        cls.env["multi.activity.tenant"].create(
            {
                "name": "Multi Est Tenant",
                "plan_id": cls.plan.id,
                "company_id": cls.company.id,
                "currency_id": cls.company.currency_id.id,
                "business_type_id": cls.btype.id,
                "state": "active",
            }
        )
        cls.est_a = cls.env["multi.activity.establishment"].create(
            {
                "name": "Site A",
                "company_id": cls.company.id,
                "business_type_id": cls.btype.id,
            }
        )
        cls.est_b = cls.env["multi.activity.establishment"].create(
            {
                "name": "Site B",
                "company_id": cls.company.id,
                "business_type_id": cls.btype.id,
            }
        )
        cls.manager = new_test_user(
            cls.env,
            login="manager_a",
            groups="multi_activity_security.group_manager",
            company_id=cls.company.id,
        )
        cls.manager.company_ids = cls.company
        cls.manager.establishment_ids = cls.est_a
        cls.est_a.user_ids = cls.manager
        category = cls.env.ref("multi_activity_operations.expense_cat_other")
        cls.expense_b = cls.env["multi.activity.expense"].create(
            {
                "establishment_id": cls.est_b.id,
                "category_id": category.id,
                "amount": 15.0,
            }
        )

    def test_manager_cannot_read_other_establishment_expense(self):
        Expense = self.env["multi.activity.expense"].with_user(self.manager)
        self.assertFalse(Expense.search([("id", "=", self.expense_b.id)]))
        with self.assertRaises(AccessError):
            self.expense_b.with_user(self.manager).read(["amount"])
