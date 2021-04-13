odoo.define('export_file_manager_it.EfmSuccess', function (require) {
    "use strict";
    
    var Notification = require('web.notification').Notification;
    var NotificationManager = require('web.notification').NotificationManager;
    var WebClient = require('web.WebClient')

    WebClient.include({
        //add efm_success event to custom_events
        custom_events: _.extend({}, WebClient.prototype.custom_events, {
            'efm_success': function (e) {
                if(this.notification_manager) {
                    this.notification_manager.efm_success(e.data.title, e.data.message, e.data.sticky);
                }
            },
        }),
    });

    // new widgets
    var EfmSuccess = Notification.extend({
        template: 'EfmSuccess',
        events: {
            'click': function (e) {
                e.preventDefault();
                this.destroy(true);
            }
        },
        start: function() {
            this._super.apply(this, arguments);
            var self = this;
            this.$el.animate({opacity: 1.0}, 400, "swing", function() {
                if(!self.sticky) {
                    setTimeout(function() {
                        self.destroy(true);
                    },5000);
                }
            });
        },
    });

    NotificationManager.include({
        efm_success: function(title, text, sticky) {
            return this.display(new EfmSuccess(this, title, text, sticky));
        },
        
    });

    return EfmSuccess;
    
    });
    