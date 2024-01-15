{
    "name": "pescini_crm",

    "summary": "Pescini CRM",

    "description": "Pescini CRM",

    "author": "Aion Tech s.r.l.",
    "website": "https://aion-tech.it/",

    "category": "Sales/CRM",
    "version": "14.0.1.0.25",

    "depends": [
        "base",
        "crm",
        "account_commission",
        "sales_team",
        "base_setup",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_view.xml",
        "views/crm_lead_view.xml",
        "views/company_classification.xml",
        "views/commission_assignments_view.xml",
        "views/crm_team_view.xml",
    ],

    "assets": {
        'web.assets_backend': [
            'pescini_crm/static/src/js/*.js',
            'pescini_crm/static/src/xml/*.xml',
        ]
    },

    "installable": True,
    "application": False,
}