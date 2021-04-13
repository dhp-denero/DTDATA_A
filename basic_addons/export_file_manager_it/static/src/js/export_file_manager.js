odoo.define('export_file_manager_it.ExportFileManager', function (require) {
    "use strict";

    var ActionManager = require('web.ActionManager');
    var framework = require('web.framework');
    var session = require('web.session');
    var crash_manager = require('web.crash_manager');
    var Model = require('web.DataModel');
    var Efm_model = new Model('export.file.manager');

    ActionManager.include({
        ir_actions_report_xml: function (action, options) {
            var self = this;
            action = _.clone(action);
            if (action.report_type === 'efm_reports') {
                // Descarga directa:
                if (action.name==='direct_download') {
                    let c = crash_manager;
                    framework.blockUI();
                    return self.session.get_file({
                        url: '/download/file/'+action.res_id,
                        complete: framework.unblockUI,
                        error: c.rpc_error.bind(c),
                        success: function () {
                            let ops = action.efm_report_options;
                            if (ops.msg_success_notify){
                                self.do_efm_success('¡Completado!',ops.msg_success_notify,true ? ops.sticky : false); 
                            }
                            if (action && options && !action.dialog) {
                                options.on_close();
                            }
                        },
                    });
                }
                // LLamar al método del objeto:
                else if(action.report_name && action.report_name.substring(0,7) === 'method_'){
                    let method_name = action.report_name.substring(7)
                    Efm_model.call('call_object_method',[action.model,method_name,action.context.active_ids])
                    .then(response => {
                        if (!response) return;
                        if (response && response.msg_success_notify) {
                            self.do_notify('¡Completado!',response.msg_success_notify)}
                        let name = response.name || false,
                            report_type = response.report_type || false,
                            efm_report_options = response.efm_report_options || {},
                            model = response.model || false,
                            res_id = response.res_id || false;
                            // NOTE siempre debe ser direct_download para preveir un infinite loop
                        if (model && report_type === 'efm_reports' && name === 'direct_download' && res_id) {
                            // recall method
                            action.model = model
                            action.report_type = report_type
                            action.efm_report_options = efm_report_options
                            action.res_id = res_id
                            action.name = name
                            action.report_name = false
                            return self.efm_recall_action(action,options)
                        }
                    })
                    .fail(err => {
                        console.error(err)
                        self.do_warn('Ocurrió un error al procesar la operación')
                    })
                }
            } else {
                return self._super(action, options);
            }
        },
        efm_recall_action: function (action,options){
            return this.ir_actions_report_xml(action,options)
        },
        do_efm_success: function(title, message, sticky) {
            this.trigger_up('efm_success', {title: title, message: message, sticky: sticky});
        },
    });
});