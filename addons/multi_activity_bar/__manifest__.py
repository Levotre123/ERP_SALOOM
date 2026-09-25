{
    "name": "Multi-Activity Bar",
    "version": "18.0.1.0.0",
    "category": "Services",
    "summary": "Bar drink units, dose conversion, and bottle stock",
    "license": "LGPL-3",
    "depends": ["multi_activity_operations", "uom"],
    "data": [
        "views/product_views.xml",
        "views/menus.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
