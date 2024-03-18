/** @odoo-module **/

import {WebsiteSale} from "website_sale.website_sale";

WebsiteSale.include({
    /**
     * Override to inject configuration session
     *
     * @override
     */
    // eslint-disable-next-line no-unused-vars
    _updateRootProduct($form, productId) {
        this._super(...arguments);
        const config_session_id = $form.find('input[name="config_session_id"]').val();
        if (config_session_id) this.rootProduct.config_session_id = config_session_id;
    },
});
