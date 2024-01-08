{
    "name": "pescini_sale",

    "summary": "Modulo custom Aion-Tech per la personalizzazione del modulo vendite.",

    "description": "Modulo custom Aion-Tech per la personalizzazione del modulo vendite.",

    "author": "Aion Tech s.r.l.",
    "website": "https://aion-tech.it/",

    'category': 'Sales/Sales',
    "version": "14.0.1.0.1",

    "depends": [
        "base",
        "sale",
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/sale_conai_views.xml',
        'views/product_template_views.xml',
    ],
    "installable": True,
    "application": False,
}