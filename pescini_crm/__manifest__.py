{
    "name": "pescini_crm",

    "summary": "Pescini CRM",

    "description": "Pescini CRM",

    "author": "Aion Tech s.r.l.",
    "website": "https://aion-tech.it/",

    "category": "Sales/CRM",
    "version": "14.0.1.0.1",

    "depends": [
        "base",
        "crm",
    ],
    "data": [
        # security/ir.model.access.csv,
        "views/res_partner_view.xml",
       "views/crm_lead_view.xml",
    ],
    "installable": True,
    "application": False,
}