{
    "name": "Multi-Activity Restaurant",
    "version": "18.0.1.0.0",
    "category": "Services",
    "summary": "Tables, restaurant orders, and kitchen states",
    "license": "LGPL-3",
    "depends": ["multi_activity_operations"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "data/ir_sequence.xml",
        "views/table_views.xml",
        "views/order_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
}
