# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_config_start(self):
        """Return action to start configuration wizard"""
        configurator_obj = self.env["product.configurator.sale"]
        ctx = dict(
            self.env.context,
            default_order_id=self.id,
            wizard_model="product.configurator.sale",
            allow_preset_selection=True,
        )
        return configurator_obj.with_context(**ctx).get_wizard_action()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    custom_value_ids = fields.One2many(
        comodel_name="product.config.session.custom.value",
        inverse_name="cfg_session_id",
        related="config_session_id.custom_value_ids",
        string="Configurator Custom Values",
    )
    config_ok = fields.Boolean(
        related="product_id.config_ok", string="Configurable", readonly=True
    )
    config_session_id = fields.Many2one(
        comodel_name="product.config.session", string="Config Session"
    )

    def reconfigure_product(self):
        """Creates and launches a product configurator wizard with a linked
        template and variant in order to re-configure a existing product. It is
        esetially a shortcut to pre-fill configuration data of a variant"""
        wizard_model = "product.configurator.sale"

        extra_vals = {
            "order_id": self.order_id.id,
            "order_line_id": self.id,
            "product_id": self.product_id.id,
        }
        self = self.with_context(
            default_order_id=self.order_id.id,
            default_order_line_id=self.id,
        )
        return self.product_id.product_tmpl_id.create_config_wizard(
            model_name=wizard_model, extra_vals=extra_vals
        )
    
    def _compute_price_unit_for_configured_products(self):
        account_tax_obj = self.env["account.tax"]
        config_price = self.config_session_id.price
        if self.order_id.pricelist_id.discount_policy == "with_discount":
            self = self.with_context(config_price=config_price)
            if not self.product_id:
                if not self.price_unit:
                    self.price_unit = config_price
                pricelist_id = self.order_id.pricelist_id._get_product_price_rule(
                    product = self.config_session_id.product_id,
                    quantity = 1.0,
                )[1]
                pricelist = self.env["product.pricelist.item"].browse(pricelist_id)
                price = pricelist.with_context(
                    config_price=config_price)._compute_base_price(
                    product = self.config_session_id.product_id, 
                    quantity = 1, 
                    uom = self.config_session_id.product_id.uom_id, 
                    date = self.order_id.date_order, 
                    target_currency = self.config_session_id.currency_id)
            else:
                price = self._get_pricelist_price()
        else:
            price = config_price

        self.price_unit = account_tax_obj._fix_tax_included_price_company(
            price,
            self.product_id.taxes_id,
            self.tax_id,
            self.company_id,
        )

    @api.depends(
        "config_session_id",
        "tax_id",
        "company_id",
    )
    def _compute_price_unit(self):
        for line in self:
            if line.config_session_id:
                return line._compute_price_unit_for_configured_products() 
            else:
                 return super(SaleOrderLine, line)._compute_price_unit()

    def _get_sale_order_line_multiline_description_variants(self):
        name = ""
        for line in self:
            custom_values = line.custom_value_ids
            if custom_values:
                name += "\n" + "\n".join(
                    [f"{cv.display_name}: {cv.value}" for cv in custom_values]
                )
            else:
                name += super(
                    SaleOrderLine,
                    line,
                )._get_sale_order_line_multiline_description_variants()
        return name
