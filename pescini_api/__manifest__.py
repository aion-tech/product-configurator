{
    "name": "pescini_api",
    "summary": "",
    "description": "",
    "author": "Aion Tech Srl",
    "website": "https://aion-tech.it/",
    # https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    "category": "Uncategorized",
    "version": "14.0.1.0.1",
    "depends": [
        "sale",
        "crm",
        "fastapi",
        "fastapi_auth_jwt",
        "auth_api_key",
        "auth_api_key_unique",
        "fastapi_auth_jwt_api_key",
        "product",
        "pescini_crm",
        "pydantic_base_model_odoo",
    ],
    "data": [
        "data/pescini_fastapi_data.xml",
        "data/jwt_validators.xml",
        "security/ir.model.access.csv",
        "security/ir_rule+acl.xml",
        "views/auth_api_views.xml",
    ],
}
