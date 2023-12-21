odoo.define('pescini_crm.CommissionAssignmentButtonInTree', function(require) {
    'use strict';

    var core = require('web.core');
    var time = require('web.time');
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var _t = core._t;
    var QWeb = core.qweb;
    var viewRegistry = require('web.view_registry');

    var CommissionAssignmentButtonInTreeController = ListController.extend({
        renderButtons: function() {
            this._super.apply(this, arguments);
            var self = this;
            this.$buttons.append($(QWeb.render('pescini_crm.commission_assignment.generate.button', this)));
            
            this.$buttons.on('click', '.commission_assignment_button', function() {
                debugger;
                self._rpc({
                    model: 'commission.assignment',
                    method: 'action_create_if_not_exist',
                    args: [[]],
                }).then(function(res) {
                    self.reload();
                    self.displayNotification({
                        title: _t('Record Creati!'),
//                        message: _.str.sprintf(_t(res)),
                        type: 'info'
                    });
                });
            });
        },
    });

    var CommissionAssignmentButtonInTreeListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: CommissionAssignmentButtonInTreeController,
        }),
    });
    viewRegistry.add('commission_assignment_button_in_list', CommissionAssignmentButtonInTreeListView);

});