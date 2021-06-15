{
    "name": "Website Product Configurator",
    "version": "14.0.1.1.0",
    "summary": """Configure products in e-shop""",
    "author": "Pledra, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/product-configurator",
    "category": "website",
    "depends": [
        "website_sale",
        "product_configurator",
        "product_configurator_sale",
    ],
    "data": [
        "security/configurator_security.xml",
        "data/ir_config_parameter_data.xml",
        "data/config_form_templates.xml",
        "data/cron.xml",
        "views/assets.xml",
        "views/product_view.xml",
        "views/templates.xml",
        "views/res_config_settings_view.xml",
    ],
    "demo": ["demo/product_template_demo.xml"],
    "images": ["static/description/cover.png"],
    "application": True,
    "installable": True,
}
