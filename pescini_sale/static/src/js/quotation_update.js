odoo.define("pescini_sale.quotation_update", function (require) {
  console.log("quotation_update");
  ("use strict");

  var publicWidget = require("web.public.widget");
  var core = require("web.core");
  var _t = core._t;

  var timeout;

  publicWidget.registry.pesciniCartLink = publicWidget.Widget.extend({
    selector: "#quotation_cart_lines_table",
    events: Object.assign({}, publicWidget.Widget.prototype.events, {
      "mouseup .js_reduce_quotation_cart_json": "_onMouseupReduceCartQty",
      "mouseup .js_add_quotation_cart_json": "_onMouseupAddCartQty",
      //   "change .js_quotation_quantity": "_onChangeQuotationOptionQuantity",
    }),
    start: function () {
      var def = this._super.apply(this, arguments);
      console.log("start");
      return def;
    },

    _onMouseupReduceCartQty: function (ev) {
      console.log("_onMouseupReduceCartQty");
      var self = this;
      var line_id = parseInt($(ev.currentTarget).attr("data-line-id"));
      var order_id = parseInt($(ev.currentTarget).attr("data-quotation-id"));
      var sign = -1;
      return this._rpc({
        route: "/quotation/cart/update",
        params: { quotation_id: order_id, order_line_id: line_id, sign: sign },
      }).then(function () {
        // Refresh the entire page
        location.reload();
      });
    },
    _onMouseupAddCartQty: function (ev) {
      console.log("_onMouseupAddCartQty");
      var self = this;
      var line_id = parseInt($(ev.currentTarget).attr("data-line-id"));
      var order_id = parseInt($(ev.currentTarget).attr("data-quotation-id"));
      var sign = 1;

      return this._rpc({
        route: "/quotation/cart/update",
        params: { quotation_id: order_id, order_line_id: line_id, sign: sign },
      }).then(function () {
        // Refresh the entire page
        location.reload();
      });
    },
    // async _onChangeQuotationOptionQuantity(ev) {
    //   console.log("_onChangeQuotationOptionQuantity");
    //   ev.preventDefault();
    //   var self = this;
    //   var line_id = parseInt($(ev.currentTarget).attr("data-line-id"));
    //   var order_id = parseInt($(ev.currentTarget).attr("data-quotation-id"));
    //   let self = this,
    //     $target = $(ev.currentTarget),
    //     sign = parseInt($target.val());

    //   return this._rpc({
    //     route: "/quotation/cart/update",
    //     params: { quotation_id: order_id, order_line_id: line_id, sign: sign },
    //   }).then(function () {
    //     // Refresh the entire page
    //     location.reload();
    //   });
    // },
  });
});
