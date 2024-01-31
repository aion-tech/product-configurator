/** @odoo-module **/
import tour from "web_tour.tour";

import websiteSaleTourUtils from "website_sale.tour_utils";

tour.register(
    "website_product_configurator.reconfigure_cart_line",
    {
        test: true,
    },
    [
        {
            content: "Add to cart",
            trigger: "#add_to_cart",
        },
        websiteSaleTourUtils.goToCart({quantity: 1}),
        {
            content: "Check Silver car is in cart",
            trigger: "#cart_products td.td-product_name strong:contains('Silver')",
            // eslint-disable-next-line no-empty-function
            run: () => {},
        },
        {
            content: "Click on reconfigure link",
            trigger: "td[class='td-reconfigure_action'] > a",
        },
        {
            content: "Check banner is shown",
            trigger: "div[role='alert']",
            // eslint-disable-next-line no-empty-function
            run: () => {},
        },
        {
            content: "Go to Body step",
            trigger: "#product_config_form a:contains('Body')",
        },
        {
            content: "Select Red color",
            // Paint color has ID 8, couldn't find a better selector
            trigger: "#__attribute_8",
            run: function () {
                const $options = $("#__attribute_8");
                const $red = $("#__attribute_8 option:contains('Red')");
                $options.val($red.attr("value")).change();
            },
        },
        {
            content: "Go to last step",
            trigger: "#product_config_form a:contains('Extras')",
        },
        {
            content: "Confirm",
            trigger: "button#form_action span:contains('Continue')",
        },
        {
            content: "Check configured car is red",
            trigger: "#product_details span:contains('Red')",
            // eslint-disable-next-line no-empty-function
            run: () => {},
        },
        {
            content: "Add to cart",
            trigger: "#add_to_cart",
        },
        {
            content: "Check banner is shown",
            trigger: "div[role='alert']",
            // eslint-disable-next-line no-empty-function
            run: () => {},
        },
        websiteSaleTourUtils.goToCart({quantity: 1}),
        {
            content: "Check Red car is in cart",
            trigger: "#cart_products td.td-product_name strong:contains('Red')",
            // eslint-disable-next-line no-empty-function
            run: () => {},
        },
    ]
);
