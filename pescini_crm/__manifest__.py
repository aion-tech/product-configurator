{
    "name": "pescini_crm",

    "summary": "Pescini CRM",

    "description": "Pescini CRM",

    "author": "Aion Tech s.r.l.",
    "website": "https://aion-tech.it/",

    "category": "Sales/CRM",
    "version": "14.0.1.0.15",

    "depends": [
        "base",
        "crm",
        "account_commission",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_view.xml",
        "views/crm_lead_view.xml",
        "views/company_classification.xml",
        # "wizard/crm_opportunity_create_contact.xml",
        "views/commission_assignments_view.xml",
    ],
    "installable": True,
    "application": False,
}
