odoo.define('web_gantt_native.ItemOptions', function (require) {
    "use strict";

    var Widget = require('web.Widget');


    var GanttListOptionsItem = Widget.extend({
        template: "GanttList.options",

        custom_events: {
            'item_order': 'order_action',
            'item_list': 'list_action',
        },

        init: function (parent) {
            this.parent = parent;
            this._super.apply(this, arguments);
        },

        start: function () {

            // if (this.default_order && !self.ItemsSorted) {
            //     this.dataset.set_sort(this.default_order.split(','));
            // }


            if (this.parent.default_order && !this.parent.ItemsSorted) {

                var default_order = this.parent.default_order.split(',');

                if (default_order.length) {
                    default_order = default_order[0].split(' ');
                }


                if (default_order) {

                    var div_ = $('<div class="text-left gantt-list-options-item"/>');
                    div_.text(this.parent.fields[default_order[0]].string);


                    var div_typer = $('<div class="fa fa-sort-amount-desc gantt-list-options-item-sort" aria-hidden="false"></div>');

                    if (default_order[1] === "asc") {
                        div_typer = $('<div class="fa fa-sort-amount-asc gantt-list-options-item-sort" aria-hidden="false"></div>');
                    }


                    div_.append(div_typer);
                    this.$el.append(div_);

                }

            }

            var item_list = $('<div class="text-left gantt-list-options-item"/>');
            item_list.text("Show List");

            var list_div = $('<div class="fa fa-square-o gantt-list-options-item-check" aria-hidden="false"></div>');
            if (this.parent.list_show) {
                list_div = $('<div class="fa fa-check-square-o gantt-list-options-item-check" aria-hidden="false"></div>');
            }


            item_list.append(list_div);
            this.$el.append(item_list);




        },


        renderElement: function () {
            this._super();

            this.$el.data('parent', this);
            this.$el.on('click', this.proxy('on_global_click'));

        },

        on_global_click: function (ev) {

            if (!ev.isTrigger) { //human detect

                if ($(ev.target).hasClass("gantt-list-options-item-sort")) {

                    this.trigger_up('item_order', {
                        default_order: this.parent.default_order,
                    });

                }

                if ($(ev.target).hasClass("gantt-list-options-item-check")) {

                    this.trigger_up('item_list', {});
                }


            }
        },

        order_action: function (event) {

            //   if (event.data.is_group && event.data.group_field == 'project_id') {
            var self = this.__parentedParent;
            // var parent = this.parent;
            // var default_order = event.data.orderedBy;

            var default_order = this.parent.default_order.split(',');
            if (default_order.length) {
                default_order = default_order[0].split(' ');
            }


            if (default_order) {


                if (default_order[1] === "asc") {
                    default_order[1] = "desc"
                } else {

                    default_order[1] = "asc"
                }
                this.parent.default_order = default_order.join(" ");

                self.do_search(self.last_domains, self.last_contexts, self.last_group_bys, self.options);

            }
        },

        list_action: function (event) {

            var self = this.__parentedParent;
            var parent = this.parent;
            // var list_show = event.data.list_show;


            if (parent.list_show) {
                parent.list_show = false
            } else {
                parent.list_show = true
            }


            self.trigger_up('gantt_fast_refresh_after_change')


        }


    });


    return {

        OptionsItem: GanttListOptionsItem

    };


});