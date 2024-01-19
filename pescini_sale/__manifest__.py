{
    "name": "pescini_sale",

    "summary": "Modulo custom Aion-Tech per la personalizzazione del modulo vendite.",

    "description": "Modulo custom Aion-Tech per la personalizzazione del modulo vendite.",

    "author": "Aion Tech s.r.l.",
    "website": "https://aion-tech.it/",

    'category': 'Sales/Sales',
    "version": "14.0.1.0.2",

    "depends": [
        "base",
        "sale",
        "account_payment", 
        "website_sale",
        "website",
        "pescini_api",
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/sale_conai_views.xml',
        'views/product_template_views.xml',
        'views/sale_portal_templates.xml',
        'views/sale_order.xml',
        # 'views/assets.xml',
    ],
    "assets": {
        'web.assets_frontend' : [
            'pescini_sale/static/src/js/quotation_update.js',
            'pescini_sale/static/src/js/quotation_tree.js',
        ]
    },
    "installable": True,
    "application": False,
}