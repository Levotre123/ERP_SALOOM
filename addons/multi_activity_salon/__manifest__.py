{
    "name": "Multi-Activity Salon",
    "version": "18.0.1.0.0",
    "category": "Services",
    "summary": "Salon and barber appointments, services, and commissions",
    "license": "LGPL-3",
    "depends": ["multi_activity_operations", "calendar", "hr"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "data/ir_sequence.xml",
        "views/appointment_views.xml",
        "views/hr_employee_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
}
