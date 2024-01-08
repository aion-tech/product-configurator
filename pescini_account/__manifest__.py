{
    "name": "pescini_account",

    "summary": "Modulo per la gestione della contabilita'",

    "description": "Modulo per la gestione della contabilita'",

    "author": "Aion Tech s.r.l.",
    "website": "https://aion-tech.it/",

    "category": "Uncategorized",
    "version": "14.0.1.0.0",

    "depends": [
        "base",
        "account_accountant",
        "sale",
    ],
    "data": [
        # security/ir.model.access.csv,
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False,
}
