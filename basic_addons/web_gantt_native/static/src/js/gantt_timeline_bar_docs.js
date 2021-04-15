odoo.define('web_gantt_native.Docs', function (require) {
    "use strict";


    var Widget = require('web.Widget');


    var GanttTimeLineDocs = Widget.extend({
        template: "GanttTimeLine.docs",

        init: function (parent) {
            this._super.apply(this, arguments);
        },


        start: function () {

            var parentg = this.getParent();

            var data_widgets = parentg.gantt_timeline_data_widget;

            _.each(data_widgets, function (widget) {

                if (!widget.record.is_group) {

                    var el = undefined;
                    var find_el = undefined;
                    var doc_el = $('<i class="fa fa-paperclip" aria-hidden="false"></i>');
                    var doc_bar = undefined;

                    var doc_count = widget.record.doc_count;

                    if (doc_count && doc_count.length) {


                        if (_.has(widget.bar_widget, "done_slider") && widget.bar_widget.done_slider) {

                            el = widget.bar_widget.done_slider[0];
                            find_el = $(el).find(".task-gantt-done-info");


                            doc_bar = $('<div class="task-gantt-docs task-gantt-docs-slider">');
                            doc_bar.append(doc_el);

                            if (find_el && find_el.length) {
                                $(find_el).append(doc_bar);
                            } else {
                                $(el).append(doc_bar);

                            }

                        } else if (_.has(widget.bar_widget, "deadline_bar") && widget.bar_widget.deadline_bar) {

                            el = widget.bar_widget.deadline_bar[0];
                            var width = parseInt($(el).css('width'));

                            doc_bar = $('<div class="task-gantt-docs task-gantt-docs-slider">');
                            doc_bar.append(doc_el);

                            doc_bar.css({"left": width + 10 + "px"});
                            doc_bar.css({"position": "absolute"});
                            $(el).append(doc_bar);

                        } else {

                            doc_bar = $('<div class="task-gantt-docs task-gantt-docs-bar">');
                            doc_bar.append(doc_el);

                            el = widget.$el;
                            find_el = $(el).find(".task-gantt-bar-plan-info-end");
                            $(find_el).before(doc_bar);
                        }

                    }

                }

                return true;
            })


        }


    });

    return {
        DocsWidget: GanttTimeLineDocs
    }

});