odoo.define("pescini_sale.quotation_tree", function (require) {
  console.log("quotation_tree");
  ("use strict");

  var publicWidget = require("web.public.widget");
  var core = require("web.core");
  var _t = core._t;

  var timeout;

  publicWidget.registry.pesciniCartLink = publicWidget.Widget.extend({
    selector: "#btn_quotations",
    events: Object.assign({}, publicWidget.Widget.prototype.events, {
      "click .js_new_quotation": "_onClickNewQuotation",
    }),
    start: function () {
      var def = this._super.apply(this, arguments);
      console.log("start");
      return def;
    },

    _onClickNewQuotation: function (ev) {
      console.log("_onClickNewQuotation");
      // alert("Creando un nuovo ordine il carrello verra' svuotato!");
      var result = confirm("Are you sure you want to proceed with the action?");
        if (result) {
            // User clicked OK
            return this._rpc({
              route: "/shop/clear",
              params: {  },
            }).then(function () {
              // Refresh the entire page
              location.href= '/shop';
            });
        } else {
            // User clicked Cancel
            alert("Cancelled!"); // You can customize the cancellation message
            // Add any additional logic you want to execute after cancellation
        }
    },

  });
});
