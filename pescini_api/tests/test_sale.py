from fastapi import status
from odoo.addons.fastapi import dependencies
from odoo.addons.fastapi.tests.common import FastAPITransactionCase
from requests import Response

from ..routers.pescini import pescini_api_router
from .common import PesciniApiTestCommon


class PesciniApiTestSale(PesciniApiTestCommon):
    def setUp(self):
        #
        NotImplementedError("TODO")
        #

        super(PesciniApiTestSale, self).setUp()
        self.partner_vals = {
            "name": "Harry Potter",
            "company": "Hogwarts School of Witchcraft and Wizardry",
            "partner_type": "società",
            "role_type": "Student",
            "email": "h.potter@hogwarts.edu",
            "phone": "02831211111",
            "vat": "",
            "street": "Hogwarts Castle, Highlands",
            "zip": "20100",
            "city": "Milano",
            "state": {"name": "Milano", "code": "MI"},
            "country": {"name": "Italy", "code": "IT"},
        }

        line_vals = [
            {
                "product_id": self.env.ref(
                    "product.product_product_6_product_template"
                ).id,
                "product_uom_qty": 3,
            },
            {
                "product_id": self.env.ref(
                    "product.product_product_9_product_template"
                ).id,
                "product_uom_qty": 7,
            },
            {
                "product_id": self.env.ref(
                    "product.product_delivery_02_product_template"
                ).id,
                "product_uom_qty": 11,
            },
        ]

    def test_sale_order(self):
        """
        Sale order creation
        """
        token = self._get_token(self.crm_api_key.key).json()["token"]
        res: Response = self._post(
            token,
            "/sale",
            self.partner_vals,
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()["status"], "ok")
        self.assertTrue(res.json()["id"])
        sale_id = self.env["sale.order"].browse(res.json()["id"])
        # partner
        self.assertEqual(
            sale_id.partner_id.name,
            self.partner_vals["name"],
        )
        self.assertEqual(
            sale_id.partner_id.company_type,
            self.partner_vals["company_type"],
        )
        self.assertEqual(
            sale_id.partner_id.company_classification.name,
            # self.partner_vals["partner_type"],
        )
        self.assertEqual(
            sale_id.partner_id.function,
            self.partner_vals["role_type"],
        )
        self.assertEqual(
            sale_id.partner_id.email,
            self.partner_vals["email"],
        )
        self.assertEqual(
            sale_id.partner_id.phone,
            self.partner_vals["phone"],
        )
        self.assertEqual(
            sale_id.partner_id.vat,
            self.partner_vals["vat"],
        )
        self.assertEqual(
            sale_id.partner_id.street,
            self.partner_vals["street"],
        )
        self.assertEqual(
            sale_id.partner_id.zip,
            self.partner_vals["zip"],
        )
        self.assertEqual(
            sale_id.partner_id.city,
            self.partner_vals["city"],
        )
        self.assertEqual(
            sale_id.partner_id.state_id.name,
            self.partner_vals["state"]["name"],
        )
        self.assertEqual(
            sale_id.partner_id.state_id.code,
            self.partner_vals["state"]["code"],
        )
        self.assertEqual(
            sale_id.partner_id.country_id.name,
            self.partner_vals["country"]["name"],
        )
        self.assertEqual(
            sale_id.partner_id.country_id.code,
            self.partner_vals["country"]["code"],
        )
        # sale order
        for line in sale_id.order_line:
            self.assertEqual(line.product_uom_qty, 0)
