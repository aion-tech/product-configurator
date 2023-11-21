{
    "name": "Aion Tech Contact From Lead",

    "summary": "Ait Contact From Lead",

    "description": "Modulo per la creazione degli utenti dal CRM.",

    "author": "Aion Tech s.r.l., Federico Medici",
    "website": "https://aion-tech.it/",

    "category": "Sales/CRM",
    "version": "14.0.1.0.1",

    "depends": [
        "base",
        "crm",
    ],
    
    "data": [
        "security/ir.model.access.csv",
        "views/crm_lead_view.xml",
        "wizard/crm_opportunity_create_contact.xml",
        "wizard/crm_lead_to_opportunity_views.xml",
    ],
    "installable": True,
    "application": False,
}

