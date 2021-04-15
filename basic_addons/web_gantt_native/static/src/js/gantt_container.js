odoo.define('web_gantt_native.GanttContainer', function (require) {
"use strict";

var core = require('web.core');
var formats = require('web.formats');
var Model = require('web.Model');
var data = require('web.data');
var time = require('web.time');
var View = require('web.View');
var form_common = require('web.form_common');
var Dialog = require('web.Dialog');

var utils = require('web.utils');

var session = require('web.session');

    var framework = require('web.framework');


var GanttTimeLineHead = require('web_gantt_native.TimeLineHead');
var GanttTimeLineHeader = require('web_gantt_native.TimeLineHeader');
var GanttTimeLineScroll = require('web_gantt_native.TimeLineScroll');


var GanttTimeLineData = require('web_gantt_native.TimeLineData');

var GanttTimeLineArrow = require('web_gantt_native.TimeLineArrow');


var GanttToolField = require('web_gantt_native.ToolField');

var GanttTimeLineGhost = require('web_gantt_native.Ghost');
var GanttTimeLineSummary = require('web_gantt_native.Summary');
var GanttTimeLineFirst = require('web_gantt_native.BarFirst');

    var GanttTimeLineInfo = require('web_gantt_native.Info');
    var GanttResourcesLevel = require('web_gantt_native.ResLevel');
    var GanttResourcesBar = require('web_gantt_native.ResBar');

    var GanttPager = require('web_gantt_native.Pager');
    var GanttListOptionsItem = require('web_gantt_native.ItemOptions');
    var GanttTimeLineDocs = require('web_gantt_native.Docs');

    var GanttListAction = require('web_gantt_native.ItemAction');
    var GanttItemzTree = require('web_gantt_native.ItemzTree');
    var GanttListInfo = require('web_gantt_native.ItemInfo');



var _t = core._t;
var _lt = core._lt;
var QWeb = core.qweb;


    // View.include({
    //
    // destroy: function () {
    //     if (!this.gantt_timeline_header_widget) {
    //
    //         var ctrl_panel = $('.timeline-gantt-h-scroll');
    //
    //
    //         // this.gantt_timeline_header_widget = [];
    //     }
    //     return this._super.apply(this, arguments);
    // },
    //
    // });

var GanttContainer = View.extend({
    display_name: _lt('Gantt APS'),
    icon: 'fa-tasks',
    template: 'GanttContainerView',
    view_type: 'ganttaps',

    events: {
        'mousedown .task-gantt-gutter': 'GutterMouseDown',
        // 'click .task-gantt-zoom-1h': 'Zoom1hClick',
        // 'click .task-gantt-zoom-2h': 'Zoom2hClick',
        // 'click .task-gantt-zoom-4h': 'Zoom4hClick',
        // 'click .task-gantt-zoom-8h': 'Zoom8hClick',
        //
        // 'click .task-gantt-zoom-days': 'ZoomDaysClick',
        // 'click .task-gantt-zoom-month': 'ZoomMonthClick',
        // 'click .task-gantt-zoom-weeks': 'ZoomWeeksClick',
        // 'click .task-gantt-zoom-quarter': 'ZoomQuarterClick',
        //
        //
        // 'click .task-gantt-today': 'ClickToday',

        'mouseover  .task-gantt-item, .task-gantt-timeline-row'     :'HandleHoverOver',
        'mouseout   .task-gantt-item, .task-gantt-timeline-row'     :'HandleHoverOut',

        'mouseover  .task-gantt-gutter'     :'GutterOver',
        'mouseout   .task-gantt-gutter'     :'GutterOut'


    },

    custom_events: {


        gantt_refresh_after_change: '_onGanttRefresh',
        gantt_fast_refresh_after_change: '_update',
        gantt_add_hover: '_add_hover',
        gantt_remove_hover: '_remove_hover',


        'sort_item': function (event) {
            this.sort_item(event.target);
        },


    },

    init: function() {
        var self = this;
        this._super.apply(this, arguments);

        this.has_been_loaded = $.Deferred();
        this.chart_id = _.uniqueId();
        this.last_data = null;
        this.scroll_today = 0;
        this.counter = 0;
        this.widgets = [];
        this.options = "all";
        this.gutterClientX  = 0;// how add need info
        this.gutterOffset = this.session.gantt || 400;
        this.gutterOffsetX = 2;
        this.timeline_width = undefined;
        this.timeScale = undefined;
        this.timeWeekPeriod = [];
        this.timeWeekSize = 0;
        this.timePrimary =  [];
        this.timeSecondary =   [];
        this.timeType = undefined;
        this.gantt_timeline_head_widget = undefined;
        this.gantt_timeline_data_widget = [];
        this.pxScaleUTC = undefined;
        this.firstDayScale = undefined;
        this.rows_to_gantt = undefined;
        this.timeScaleUTC = undefined;


        // this.firstDay = undefined;
        // this.lastDay = undefined;

        this.firstDayDate = undefined;
        this.lastDayDate = undefined;


        this.GtimeStartA = [];
        this.GtimeStopA = [];

        this.GtimeStart = undefined;
        this.GtimeStop = undefined;


        //this.BarMovieX = undefined;
        this.BarMovieValue = undefined;
        this.BarClickDiffX = undefined;
        this.BarClickX = undefined;

        this.BarRecord= undefined;

        this.BarClickDown = false;

        this.BarWidth = undefined;

        this.ABarWidth = undefined;
        this.ABarLeft = undefined;
        this.TimeToLeft = false;

        this.ItemsSorted = false;

        this.hint_move_widget = undefined;
        this.tip_move_widget = undefined;

        this.hover_id = undefined;

        this.ScrollToTop = undefined;


        this.Predecessor = undefined;


        this.main_group_id_name = undefined;


        this.GanttPager = undefined;
        this.pager = [];


        // Sort
        this.default_order = this.fields_view.arch.attrs.default_order;

        this.list_show = false;






    },

    normalizeGutterOffset: function(offset) {
	    var minOffset = 2;
	    var maxOffset = $('.gantt-container').width() - 100;
	    return Math.min(Math.max(offset, minOffset), maxOffset > minOffset ? maxOffset : minOffset);
    },

    //Odoo9.0
    // view_loading: function(r) {
    //     return this.load_gantt(r);
    // },


    // load_gantt: function(fields_view_get, fields_get) {
    //     var self = this;
    //     self.main_group_id_name = this.fields_view.arch.attrs.main_group_id_name;
    //     this.fields_view = fields_view_get;
    //     this.$el.addClass(this.fields_view.arch.attrs['class']);
    //     return self.alive(new Model(this.dataset.model)
    //         .call('fields_get')).then(function (fields) {
    //             self.fields = fields;
    //             self.has_been_loaded.resolve();
    //         });
    // },

    willStart: function() {
        var self = this;

        //get options from xml for main group
        self.main_group_id_name = this.fields_view.arch.attrs.main_group_id_name;

        self.action_menu = this.fields_view.arch.attrs.action_menu;

        this.$el.addClass(this.fields_view.arch.attrs['class']);
        return self.alive(new Model(this.dataset.model)
            .call('fields_get')).then(function (fields) {
                self.fields = fields;
                self.has_been_loaded.resolve();
            });
    },


    render_pager: function ($node, options) {

        var data = [];

        data["size"] = this.pager.records;
        data["limit"] = this.pager.limit;


        this.GanttPager = new GanttPager(this, data.size, data.limit, options);

        this.GanttPager.on('pager_changed', this, function (newState) {
            var self = this;
            self.GanttPager.disable();

            self.pager.limit = parseInt(newState.limit);

            this.reload().then(self.GanttPager.enable.bind(self.GanttPager));

        });
        this.GanttPager.appendTo($node);

    },

    render_buttons: function ($node) {
        if ($node) {
            var context = {measures: _.pairs(_.omit(this.measures, '__count__'))};
            this.$buttons = $(QWeb.render('APSGanttView.buttons', context));
            this.$buttons.click(this.on_button_click.bind(this));
            // this.$measure_list = this.$buttons.find('.o_graph_measures_list');
            // this.update_measure();
            // this.$buttons.find('button').tooltip();
            // this.$buttons.click(this.on_button_click.bind(this));

            // this.$buttons.find('.o_graph_button[data-mode="' + this.widget.mode + '"]').addClass('active');

            this.$buttons.appendTo($node);
        }
    },

    on_button_click: function (event) {
        var $target = $(event.target);
        if ($target.hasClass('task-gantt-today')) { return this.ClickToday(); }

        if ($target.hasClass('task-gantt-zoom-1h')) { return this.Zoom1hClick(); }
        if ($target.hasClass('task-gantt-zoom-2h')) { return this.Zoom2hClick(); }
        if ($target.hasClass('task-gantt-zoom-4h')) { return this.Zoom4hClick(); }
        if ($target.hasClass('task-gantt-zoom-8h')) { return this.Zoom8hClick(); }
        if ($target.hasClass('task-gantt-zoom-days')) { return this.ZoomDaysClick(); }
        if ($target.hasClass('task-gantt-zoom-month')) { return this.ZoomMonthClick(); }
        if ($target.hasClass('task-gantt-zoom-weeks')) { return this.ZoomWeeksClick(); }
        if ($target.hasClass('task-gantt-zoom-quarter')) { return this.ZoomQuarterClick(); }


        // 'click .task-gantt-zoom-1h': 'Zoom1hClick',
        // 'click .task-gantt-zoom-2h': 'Zoom2hClick',
        // 'click .task-gantt-zoom-4h': 'Zoom4hClick',
        // 'click .task-gantt-zoom-8h': 'Zoom8hClick',
        //
        // 'click .task-gantt-zoom-days': 'ZoomDaysClick',
        // 'click .task-gantt-zoom-month': 'ZoomMonthClick',
        // 'click .task-gantt-zoom-weeks': 'ZoomWeeksClick',
        // 'click .task-gantt-zoom-quarter': 'ZoomQuarterClick',

        // if ($target.hasClass('o_pivot_expand_button')) { return this.expand_all(); }
        // if ($target.parents('.o_pivot_measures_list').length) {
        //     var parent = $target.parent();
        //     var field = parent.data('field');
        //     parent.toggleClass('selected');
        //     event.preventDefault();
        //     event.stopPropagation();
        //     return this.toggle_measure(field);
        // }
        // if ($target.hasClass('o_pivot_download')) {
        //     return this.download_table();
        // }
    },

    _onGanttRefresh: function (event) {
        var self = this;

        self.reload();
    },

    //---1---//
    do_search: function (domains, contexts, group_bys, options) {


        var self = this;

        // Sort allow only if Group by project and domain search by project.
        // Project get from XML = main_group_id_name = "project_id"
        self.ItemsSorted = false;
        if (group_bys.length == 1){

            if (group_bys[0] === self.main_group_id_name) {
                 self.ItemsSorted = true;
            }
            if (domains.length > 0){
                if (domains[0][0] !== self.main_group_id_name) {
                 self.ItemsSorted = false;
                }
            }

            if (domains.length > 1){
                self.ItemsSorted = false;
            }
        }

        if (self.fields_view.arch.attrs.no_group_sort_mode){
            self.ItemsSorted = false;
        }

        // Tree View only if group by main_group_id_name
        self.TreeView = false;

        if (group_bys.length === 1) {

            if (group_bys[0] === self.main_group_id_name || group_bys[-1] === self.main_group_id_name) {
                self.TreeView = true;
            }
        }

        if (group_bys.length > 1) {

            if (group_bys[group_bys.length - 1] === self.main_group_id_name) {
                self.TreeView = true;
            }
        }



        self.ExportWizard = false;
        if (self.fields_view.arch.attrs.hasOwnProperty('export_wizard')) {
            self.ExportWizard = self.fields_view.arch.attrs.export_wizard
        }


        self.options = options || 'all';
        self.last_domains = domains;
        self.last_contexts = contexts;
        self.last_group_bys = group_bys;
        self.date_start = null;
        self.date_stop = null;

        var n_group_bys = [];

        // select the group by - we can select group by from attribute where XML if not determinate dafault group
        // for model

        if (this.fields_view.arch.attrs.default_group_by) {
           n_group_bys = this.fields_view.arch.attrs.default_group_by.split(',');
        }

        if (group_bys.length) {
            n_group_bys = group_bys;
        }


        var getFields = GanttToolField.getFields(self, group_bys);
        self.model_fields = getFields["model_fields"];
        self.model_fields_dict = getFields["model_fields_dict"];

        // var limit_view = 0;
        // if (this.fields_view.arch.attrs.hasOwnProperty('limit_view')) {
        //     limit_view = parseInt(this.fields_view.arch.attrs.limit_view)
        // }
        //
        // if (self.pager.limit) {
        //     limit_view = self.pager.limit
        // }


        //Pager
        var limit_view = 0;
        if (self.fields_view.arch.attrs.hasOwnProperty('limit_view')) {
            limit_view = parseInt(self.fields_view.arch.attrs.limit_view)
        }

        if (self.pager.limit) {
            limit_view = self.pager.limit
        }


        //Load Level
        var load_group_id_name = self.fields_view.arch.attrs.load_group_id_name;
        self.LoadMode = false;
        if (group_bys.length === 1) {

            if (group_bys[0] === load_group_id_name || group_bys[-1] === load_group_id_name) {
                self.LoadMode = true;
            }
        }

        if (group_bys.length > 1) {

            if (group_bys[group_bys.length - 1] === load_group_id_name) {
                self.LoadMode = true;
            }
        }



        // Options wise view loading [Year, Month, Week]

        if (self.options == 'all') {
            self.domains = domains;
        }


        // var unsorted = !this.dataset._sort.length;
        if (this.default_order && !self.ItemsSorted) {
            this.dataset.set_sort(this.default_order.split(','));
        }
        //
        //
        //
        // if (self.dataset._sort) {
        //     self.dataset.set_sort(self.dataset._sort);
        // }


        return $.when(this.has_been_loaded).then(function() {
            return self.dataset.read_slice(self.model_fields, {
                domain: domains,
                context: contexts,
                limit: limit_view
            }).then(function(data) {
                if (data.length) {
                    self.pager.limit = limit_view;
                    return self.on_data_loaded_count(data, n_group_bys, domains, contexts);

                } else {

                    return alert('No data found...');
                }
            });
        });


    },


    on_data_loaded_count: function (tasks, group_bys, domains, contexts) {
        var self = this;

        return $.when(this.has_been_loaded).then(function () {
            return self.dataset.call('search_count', [domains, contexts]).then(function (data) {

                self.pager.records = data;

                if (self.pager.records > self.pager.limit) {
                    self.ItemsSorted = false
                }
                return self.on_data_loaded_dummy(tasks, group_bys);


            });
        });


    },


    on_data_loaded_dummy: function(tasks, group_bys) {
        var self = this;

        return self.on_data_loaded_info(tasks, group_bys);

    },


    on_data_loaded_info: function (tasks, group_bys) {
        var self = this;
        var ids = _.pluck(tasks, "id");

        var info_model = self.fields_view.arch.attrs.info_model;
        var info_task_id = "task_id";


        if (info_model) {

            var dataset = new data.DataSetSearch(self, info_model, session.context, [[info_task_id, 'in', _.uniq(ids)]]);

            dataset.read_slice([info_task_id, "start", "end", "left_up", "left_down", "right_up", "right_down", "show"]).then(function (result) {
                return result;
            }).then(function (result) {

                if (result) {
                    result = _.map(result, function (info) {

                        if (info.task_id) {
                            info.task_id = info.task_id[0];
                            return info;
                        }
                    });
                }

                self.Task_Info = result;
                return self.on_data_loaded_predecessor(tasks, group_bys);

            })
        } else {
            return self.on_data_loaded_predecessor(tasks, group_bys);
        }

    },




    //Fist Entry poin load predecessor after. get atributes from XML
    on_data_loaded_predecessor: function(tasks, group_bys) {
        var self = this;
        var ids = _.pluck(tasks, "id");

        var predecessor_model = self.fields_view.arch.attrs.predecessor_model;
        var predecessor_task_id = self.fields_view.arch.attrs.predecessor_task_id;
        var predecessor_parent_task_id = self.fields_view.arch.attrs.predecessor_parent_task_id;
        var predecessor_type = self.fields_view.arch.attrs.predecessor_type;

        if (predecessor_model) {

            var dataset = new data.DataSetSearch(self, predecessor_model, session.context, [[predecessor_task_id, 'in', _.uniq(ids)]]);

            dataset.read_slice([predecessor_task_id, predecessor_parent_task_id, predecessor_type]).then(function (result) {
                return result;
            }).then(function (result) {
                self.Predecessor = result;
                return self.on_data_loaded_ghost(tasks, group_bys);
            })
        }
        else{
            return self.on_data_loaded_ghost(tasks, group_bys);
        }

    },

        //Fist Entry poin load predecessor after. get atributes from XML
    on_data_loaded_ghost: function(tasks, group_bys) {
        var self = this;
        var ids = _.pluck(tasks, "id");

        var ghost_id = self.fields_view.arch.attrs.ghost_id;
        var ghost_model = self.fields_view.arch.attrs.ghost_model;
        var ghost_name = self.fields_view.arch.attrs.ghost_name;
        var ghost_date_start = self.fields_view.arch.attrs.ghost_date_start;
        var ghost_date_end = self.fields_view.arch.attrs.ghost_date_end;
        var ghost_durations = self.fields_view.arch.attrs.ghost_durations;

        if (ghost_model) {

            var dataset = new data.DataSetSearch(self, ghost_model, session.context, [[ghost_id, 'in', _.uniq(ids)]]);

            dataset.read_slice([ghost_id ,ghost_name, ghost_date_start, ghost_date_end, ghost_durations]).then(function (result) {
                return result;

            }).then(function (result) {
                self.Ghost = result;
                self.Ghost_Data = GanttTimeLineGhost.get_data_ghosts(self);

                return self.on_data_loaded_barfirst(tasks, group_bys);
            })
        }
        else{
            return self.on_data_loaded_barfirst(tasks, group_bys);
        }

    },

    on_data_loaded_barfirst: function(tasks, group_bys) {

        var self = this;

        if (self.ItemsSorted) {

            var barfirst_field = "project_id";


            var barfirst_field_ids = _.pluck(tasks, "project_id");

            var ids = _.pluck(barfirst_field_ids, "0");

            var barfirst_model = "project.project";
            var barfirst_name = "name";
            var barfirst_date_start = "date_start";
            var barfirst_date_end = "date_end";

            var dataset = new data.DataSetSearch(self, barfirst_model, session.context, [['id', 'in', _.uniq(ids)]]);

            dataset.read_slice(['id', barfirst_name, barfirst_date_start, barfirst_date_end]).then(function (result) {
                return result;

            }).then(function (result) {
                self.BarFirst = result;
                self.BarFirst_Data = GanttTimeLineFirst.get_data_barfirst(self);

                return self.on_data_loaded_name_get(tasks, group_bys);
            })
        }
        else{
            return self.on_data_loaded_name_get(tasks, group_bys);
        }

    },



    //Get name get from model form name field
    on_data_loaded_name_get: function(tasks, group_bys) {
        var self = this;
        var ids = _.pluck(tasks, "id");


        self.dataset.name_get(ids).then(function(names) {

            var ntasks = _.map(tasks, function(task) {
                    return _.extend({__name: _.detect(names, function(name) { return name[0] == task.id; })[1]}, task);
            });

            return self.get_second_sort_data(ntasks, group_bys);
        });

    },


    get_second_sort_data: function (tasks, group_bys) {

        var self = this;
        self.gantt_data_second_sort = undefined;
        var gantt_attrs = self.fields_view.arch.attrs;

        var link_field = gantt_attrs["second_seq_link_field"];

        if (group_bys.length === 1 && group_bys[0] === link_field) {

            var ids = [];
            _.map(tasks, function (result) {

                if (result[link_field]) {
                    ids.push(result[link_field][0]);
                }
            });

            var s_model = gantt_attrs["second_seq_model"];
            var s_field = gantt_attrs["second_seq_field"];

            var dataset = new data.DataSetSearch(self, s_model, session.context, [['id', 'in', _.uniq(ids)]]);

            dataset.read_slice(['id', s_field]).then(function (result) {
                return result;

            }).then(function (result) {
                self.gantt_data_second_sort = result;

                return self.get_minmax_step(tasks, group_bys);
            });
        } else {
            return self.get_main_group_data(tasks, group_bys);
        }

    },


// return self.gantt_render(tasks, group_bys);

    // return self.get_main_group_data(tasks, group_bys);

    get_main_group_data: function (tasks, group_bys) {

        var self = this;
        self.gantt_data_main_group = undefined;
        var gantt_attrs = self.fields_view.arch.attrs;

        var main_id = gantt_attrs["main_group_id_name"];
        var s_model = gantt_attrs["main_group_model"];
        var s_field = ["id", "name", "fold"];

        if (group_bys.length === 1 && group_bys[0] === main_id && s_model) {

            var ids = [];
            _.map(tasks, function (result) {

                if (result[main_id]) {
                    ids.push(result[main_id][0]);
                }
            });

            var dataset = new data.DataSetSearch(self, s_model, session.context, [['id', 'in', _.uniq(ids)]]);
            dataset.read_slice(s_field).then(function (result) {
                return result;

            }).then(function (result) {
                self.gantt_data_main_group = result;
                return self.get_minmax_step(tasks, group_bys);
            });
        } else {
            return self.get_minmax_step(tasks, group_bys);
        }

    },

    get_minmax_step: function (tasks, group_bys) {
        var self = this;

        var parent = {};

        // var getFields = GanttToolField.getFields(self, group_bys);
        // self.model_fields = getFields["model_fields"];
        // self.model_fields_dict = getFields["model_fields_dict"];

        // parent.fields = self.gantt.fields;
        //
        // parent.model_fields_dict = self.gantt.data.model_fields_dict;
        // parent.gantt_attrs = self.gantt.data.model_fields_view.arch.attrs;
        // parent.second_sort = self.gantt.data.second_sort;
        // parent.main_group = self.gantt.data.main_group;

        // //Group Rows
        // var groupRows = GanttToolField.groupRows(tasks, group_bys, self);
        //
        // //Get all tasks with group
        // self.projects = groupRows["projects"];
        //
        // //Get Max Min date for data
        // self.GtimeStopA = self.GtimeStopA.concat(groupRows["timestop"]);
        // self.GtimeStartA = self.GtimeStartA.concat(groupRows["timestart"]);
        //
        // //Calc Min - Max
        // self.GtimeStart = Math.min.apply(null, self.GtimeStartA); // MAX date in date range
        // self.GtimeStop = Math.max.apply(null, self.GtimeStopA); // Min date in date range
        // //Clean
        // self.GtimeStartA = [];
        // self.GtimeStopA = [];


        var groupRows = GanttToolField.groupRows(tasks, group_bys, self);
        // self.gantt.data["projects"] = groupRows["projects"];

        self.gantt_data_rows_to_gantt = GanttToolField.flatRows(groupRows["projects"], self.ItemsSorted);

        //Get Max Min date for data
        var GtimeStartA = groupRows["timestart"];
        var GtimeStopA = groupRows["timestop"];


        self.gantt_data_GtimeStart = Math.min.apply(null, GtimeStartA); // MAX date in date range
        self.gantt_data_GtimeStop = Math.max.apply(null, GtimeStopA); // Min date in date range

        // GtimeStopA = [];
        // GtimeStartA = [];

        return self.get_res_task_load(tasks, group_bys);


    },

    get_res_task_load: function (tasks, group_bys) {
        var self = this;

        var gantt_attrs = self.fields_view.arch.attrs;

        var load_model = gantt_attrs["load_bar_model"];
        var load_id = gantt_attrs["load_id"];
        var load_id_from = gantt_attrs["load_id_from"];
        var load_ids_from = gantt_attrs["load_ids_from"];

        var ids = false;
        if (load_ids_from === "id") {

            ids = _.pluck(tasks, "id");

        } else if (load_ids_from !== "" && load_ids_from !== undefined) {

            var gp_load = _.map(tasks, function (group_value) {
                if (group_value[load_ids_from] !== false && group_value[load_ids_from] !== undefined && group_value[load_ids_from].length > 0) {
                    return group_value[load_ids_from][0]
                }

                // if (group_value[load_id] !== false && group_value[load_id].length == 1 ){
                //     return group_value[load_id]
                // }

            });

            ids = _.compact(gp_load);

        }


        if (ids) {
            var _fields = [load_id, load_id_from, 'data_from', 'data_to', 'data_aggr', 'duration'];
            var _domain = [[load_id_from, 'in', _.uniq(ids)]];

            var dataset = new data.DataSetSearch(
                self,
                load_model,
                session.context,
                _domain);


            dataset.read_slice(_fields).then(function (result) {
                return result;

            }).then(function (result) {
                self.Task_Load_Data = result;
                return self.get_res_load(tasks, group_bys);
            });
        } else {
            return self.gantt_render(tasks, group_bys);
        }


    },


    get_res_load: function (tasks, group_bys) {

        var self = this;


        if (self.LoadMode) {

            // var _contexts = self.gantt.contexts;

            // var _ctx = {
            //         'group_by': 'data_aggr',
            //         'lang': _contexts.lang,
            //         'tz': _contexts.tz,
            //         'uid': _contexts.uid
            // };
            var gantt_attrs = self.fields_view.arch.attrs;
            var load_model = gantt_attrs["load_bar_model"];
            var _ctx = session.context;

            var m_GtimeStart = moment(self.gantt_data_GtimeStart).format("YYYY-MM-DD");
            var m_GtimeStop = moment(self.gantt_data_GtimeStop).format("YYYY-MM-DD");
            // var _domain = [['data_aggr', '>=', m_GtimeStart], ['data_aggr', '<=', m_GtimeStop]];

            var data_load_group = _.where(self.gantt_data_rows_to_gantt, {is_group: true});

            var gp_load = _.map(data_load_group, function (group_value) {
                if (group_value.group_id !== false && group_value.group_id.length > 0) {
                    return group_value.group_id[0]
                }
            });

            var gp_domain_ids = _.compact(gp_load);
            var _domain = [['resource_id', 'in', _.uniq(gp_domain_ids)], ['data_aggr', '>=', m_GtimeStart], ['data_aggr', '<=', m_GtimeStop]];
            var _fields = ['task_id', 'data_from', 'data_to', 'user_id', 'data_aggr', 'duration', 'resource_id'];

            // project.task.detail.plan
            // project.task.detail.plan.res.link
            var dataset = new data.DataSetSearch(
                self,
                load_model,
                session.context,
                _domain);
            dataset.read_slice(_fields).then(function (result) {
                return result;

            }).then(function (result) {
                self.Load_Data = result;
                return self.gantt_render(tasks, group_bys);
            });
        } else {
            return self.gantt_render(tasks, group_bys);
        }


    },



    reload: function () {
        var self = this;

        return self.do_search(self.last_domains, self.last_contexts, self.last_group_bys, self.options);

    },


    _update: function () {
        var self = this;

        //Get Zoom Event from time scale type

        if (self.timeType === 'month_day'){
            self.ZoomDaysClick();
        }

        if (self.timeType === 'day_1hour'){
            self.Zoom1hClick();
        }
        if (self.timeType === 'day_2hour'){
            self.Zoom2hClick();
        }
        if (self.timeType === 'day_4hour'){
            self.Zoom4hClick();
        }
        if (self.timeType === 'day_8hour'){
            self.Zoom8hClick();
        }

        if (self.timeType === 'year_month'){

             self.ZoomMonthClick();
        }

        if (self.timeType === 'month_week'){

             self.ZoomWeeksClick();
        }
        if (self.timeType === 'quarter'){

             self.ZoomQuarterClick();
        }




        //Update

        //Get Getter offset from session
        $('.task-gantt-list').width(self.session.gantt || self.gutterOffset);

        //Hover selected rows after refresh page
        var rowdata = '#task-gantt-timeline-row-'+self.hover_id;
        var rowitem = '#task-gantt-item-'+self.hover_id;

        $(rowdata).addClass("task-gantt-timeline-row-hover");
        $(rowitem).addClass("task-gantt-item-hover");


        // Goto Vertial and Horizontal Scroll
        if (self.TimeToLeft) {
            var task_left = self.TimeToLeft;
            $('.task-gantt-timeline').animate({
                scrollLeft: task_left
                }, 0, function() {
            // Animation complete.
            });
            $('.timeline-gantt-head').animate({
                scrollLeft: task_left
                }, 0, function() {
            // Animation complete.
            });


            self.gantt_timeline_scroll_widget.scrollOffset(task_left);


        }

        if (self.ScrollToTop) {
           var panel_top = self.ScrollToTop;
            $('.task-gantt').animate({
                scrollTop: panel_top
                }, 0, function() {
            // Animation complete.
          });
        }


        if (this.GanttPager) {
            this.GanttPager.refresh(this.pager.records, this.pager.limit);
        }


    },

    gantt_render: function (tasks, group_bys) {
        var self = this;

        //Group Rows
        // var groupRows = GanttToolField.groupRows(tasks, group_bys, self);
        //
        // //Get all tasks with group
        // self.projects = groupRows["projects"];
        //
        // //Get Max Min date for data
        // self.GtimeStopA = self.GtimeStopA.concat(groupRows["timestop"]);
        // self.GtimeStartA = self.GtimeStartA.concat(groupRows["timestart"]);
        //
        // //Calc Min - Max
        // self.GtimeStart = Math.min.apply(null, self.GtimeStartA); // MAX date in date range
        // self.GtimeStop = Math.max.apply(null, self.GtimeStopA); // Min date in date range
        // //Clean
        // self.GtimeStartA = [];
        // self.GtimeStopA = [];

        self.GtimeStart = self.gantt_data_GtimeStart;
        self.GtimeStop = self.gantt_data_GtimeStop;


        //set time scale type if is undefined
        if (self.timeType === undefined) {
            self.timeType = 'month_day';
        }

        //Gantt Conteriner Render.
        self.$el.html(QWeb.render('GanttContainerView.main', {
            'title': "My Table",
            'widget': self,
            'display_name': this.display_name,
            'gutterOffset': this.gutterOffset,

        }));

        //Sorted and grouped to flat list
        self.rows_to_gantt = self.gantt_data_rows_to_gantt;
        //GanttToolField.flatRows(self.projects);


        // Start - End month
        self.firstDayDate = moment(self.GtimeStart).clone().startOf('month'); //Start month
        self.lastDayDate = moment(self.GtimeStop).clone().endOf('month'); //End month
        self.timeScaleUTC = self.lastDayDate.valueOf() - self.firstDayDate.valueOf(); // raznica vremeni
        self.firstDayScale = self.firstDayDate.valueOf();

        //Sorted Item if sorted allow
        var options = {
            items_sorted: self.ItemsSorted,
            export_wizard: self.ExportWizard,
            main_group_id_name: self.main_group_id_name,
            tree_view: self.TreeView,
            action_menu: self.action_menu,

        };

        self.widget_ztree = new GanttItemzTree(self, self.rows_to_gantt, options);
        self.widget_ztree.appendTo(self.$('.task-gantt-items'));


        self._update();


    },


    AddItemsData: function () {
        var self = this;


        //Item Action
        if (self.widget_item_action) {
            this.widget_item_action.destroy();
            self.widget_item_action = [];
        }

        var options = {
            items_sorted: self.ItemsSorted,
            export_wizard: self.ExportWizard,
            main_group_id_name: self.Main_Group_Id_Name,
            tree_view: self.TreeView,
            action_menu: self.Action_Menu,
        };


        self.widget_item_action = new GanttListAction(self, options);
        self.widget_item_action.appendTo(self.$('.task-gantt-action'));


        //Item Info
        if (self.widget_item_info) {
            this.widget_item_info.destroy();
            self.widget_item_info = [];
        }

        self.widget_item_info = new GanttListInfo(self, options);
        self.widget_item_info.appendTo(self.$('.task-gantt-info'));


    },


    AddTimeLineArrow: function( timeline_width ) {

        var self = this;
        if (self.gantt_timeline_arrow_widget){
            this.gantt_timeline_arrow_widget.destroy();
            self.gantt_timeline_arrow_widget = [];
        }

        this.gantt_timeline_arrow_widget = new GanttTimeLineArrow(self, timeline_width );
        this.gantt_timeline_arrow_widget.appendTo(self.$('.task-gantt-timeline-inner'));

    },


    AddTimeLineHead: function(timeScale, time_type, time_month, time_day ) {

        var self = this;
        if (this.gantt_timeline_head_widget){
            this.gantt_timeline_head_widget.destroy();
        }

        this.gantt_timeline_head_widget = new GanttTimeLineHead(self, timeScale, time_type, time_month, time_day  );
        this.gantt_timeline_head_widget.appendTo(self.$('.task-gantt-timeline-inner'));


        if (this.gantt_timeline_header_widget){
            this.gantt_timeline_header_widget.destroy();
            this.gantt_timeline_header_widget = [];
        }

        this.gantt_timeline_header_widget = new GanttTimeLineHeader(self, timeScale, time_type, time_month, time_day  );

        // var ctrl_panel = $('.o_control_panel');
        var ctrl_panel = $('.timeline-gantt');
        this.gantt_timeline_header_widget.appendTo(ctrl_panel);

        if (this.gantt_item_options_widget) {
            this.gantt_item_options_widget.destroy();
            this.gantt_item_options_widget = [];
        }
        this.gantt_item_options_widget = new GanttListOptionsItem.OptionsItem(self);
        this.gantt_item_options_widget.appendTo(self.$('.timeline-gantt-options'));


        if (this.gantt_timeline_scroll_widget){
            this.gantt_timeline_scroll_widget.destroy();
            this.gantt_timeline_scroll_widget = [];
        }


        this.gantt_timeline_scroll_widget = new GanttTimeLineScroll(self, timeScale, time_type, time_month, time_day  );

        // var ctrl_panel = $('.o_control_panel');
        var scroll_panel = $('.timeline-gantt-scroll');
        this.gantt_timeline_scroll_widget.appendTo(scroll_panel);



        // Goto Horizontal Scroll
        if (this.TimeToLeft) {
            var task_left = this.TimeToLeft;
            $('.task-gantt-timeline').animate({
                scrollLeft: task_left
                }, 0, function() {
            // Animation complete.
            });
            $('.timeline-gantt-head').animate({
                scrollLeft: task_left
                }, 0, function() {
            // Animation complete.
            });

            self.gantt_timeline_scroll_widget.scrollOffset(task_left);


        }

    },


     AddTimeLineData: function(timeScale, time_type, rows_to_gantt ) {

        var self = this;
        if (this.gantt_timeline_data_widget.length > 0){
            this.gantt_timeline_data_widget = [];
           //  _.each(this.gantt_timeline_data_widget, function(data_widget) {
           //      data_widget.destroy();
           //  })
        }


         var $zTree = self.widget_ztree.$zTree;
         var options = {items_sorted: self.ItemsSorted, tree_view: self.TreeView};
         var nodes = $zTree.getNodes();

         _.each(nodes, function (node) {

             var childNodes = $zTree.transformToArray(node);

             _.each(childNodes, function (child) {

                 var gantt_time_line_data = new GanttTimeLineData(self, timeScale, time_type, child, options);

                 gantt_time_line_data.appendTo(self.$('.task-gantt-timeline-data'));
                 self.gantt_timeline_data_widget.push(gantt_time_line_data);


             })
         });


         // _.map(rows_to_gantt, function (record) {
         //
         //     var options = {items_sorted: self.ItemsSorted};
         //
         //     var gantt_time_line_data = new GanttTimeLineData(self, timeScale, time_type, record, options);
         //
         //      gantt_time_line_data.appendTo(self.$('.task-gantt-timeline-data'));
         //      self.gantt_timeline_data_widget.push(gantt_time_line_data);
         // });

     },

    AddTimeLineGhost: function() {

        //Ghost
        var self = this;
        if (self.gantt_timeline_ghost_widget){
            this.gantt_timeline_ghost_widget.destroy();
            self.gantt_timeline_ghost_widget = [];
        }

        this.gantt_timeline_ghost_widget = new GanttTimeLineGhost.GhostWidget(self);
        this.gantt_timeline_ghost_widget.appendTo(self.$('.task-gantt-timeline-data'));

        //Info
        if (self.gantt_timeline_info_widget) {
            this.gantt_timeline_info_widget.destroy();
            self.gantt_timeline_info_widget = [];
        }

        this.gantt_timeline_info_widget = new GanttTimeLineInfo.InfoWidget(self);
        this.gantt_timeline_info_widget.appendTo(self.$('.task-gantt-bar-plan'));

        //Resources Level
        if (self.gantt_timeline_res_level_widget) {
            this.gantt_timeline_res_level_widget.destroy();
            self.gantt_timeline_res_level_widget = [];
        }
        this.gantt_timeline_res_level_widget = new GanttResourcesLevel.ResLevelWidget(self);
        this.gantt_timeline_res_level_widget.appendTo(self.$('.task-gantt-timeline-data'));


        //Detail Task
        //Resources Level
        if (self.gantt_timeline_res_bar_widget) {
            this.gantt_timeline_res_bar_widget.destroy();
            self.gantt_timeline_res_bar_widget = [];
        }
        this.gantt_timeline_res_bar_widget = new GanttResourcesBar.ResBarWidget(self);
        this.gantt_timeline_res_bar_widget.appendTo(self.$('.task-gantt-timeline-data'));


        //Docs
        if (self.gantt_timeline_docs_widget) {
            this.gantt_timeline_docs_widget.destroy();
            self.gantt_timeline_docs_widget = [];
        }
        this.gantt_timeline_docs_widget = new GanttTimeLineDocs.DocsWidget(self);
        this.gantt_timeline_docs_widget.appendTo(self.$('.task-gantt-timeline-data'));



    },

    AddTimeLineSummary: function() {

        var self = this;
        if (self.gantt_timeline_summary_widget){
            this.gantt_timeline_summary_widget.destroy();
            self.gantt_timeline_summary_widget = [];
        }

        this.gantt_timeline_summary_widget = new GanttTimeLineSummary.SummaryWidget(self);
        this.gantt_timeline_summary_widget.appendTo(self.$('.task-gantt-timeline-data'));

    },

    AddTimeLineFirst: function() {

        var self = this;
        if (self.gantt_timeline_first_widget){
            this.gantt_timeline_first_widget.destroy();
            self.gantt_timeline_first_widget = [];
        }

        this.gantt_timeline_first_widget = new GanttTimeLineFirst.BarFirstWidget(self);
        this.gantt_timeline_first_widget.appendTo(self.$('.task-gantt-timeline-data'));

    },


//Zoom Out - Zoom In



    Zoom1hClick: function() {
        this.ZoomHoursClick(1, 'day_1hour' );
        // this.timeType = 'day_1hour';
    },
    Zoom2hClick: function() {
        this.ZoomHoursClick(2, 'day_2hour');
        // this.timeType = 'day_2hour';
    },
    Zoom4hClick: function() {
        this.ZoomHoursClick(4, 'day_4hour');
        // this.timeType = 'day_4hour';
    },
    Zoom8hClick: function() {
        this.ZoomHoursClick(8, 'day_8hour');
        // this.timeType = 'day_8hour';
    },



    ZoomHoursClick: function(div_hour, timeType) {

                this.firstDayDate = moment(this.GtimeStart).clone().startOf('month'); //Start month
        this.lastDayDate = moment(this.GtimeStop).clone().endOf('month'); //End
        this.timeScaleUTC = this.lastDayDate.valueOf() - this.firstDayDate.valueOf(); // raznica vremeni
        this.firstDayScale = this.firstDayDate.valueOf();

        var iter = moment(this.firstDayDate).twix(this.lastDayDate).iterate(div_hour, 'hours');

        var hour2Range=[];
        while(iter.hasNext()){

             hour2Range.push(iter.next().toDate())

        }


        var daysGroup = _(hour2Range).groupBy(function (day) {
             return moment(day).format("YYYY MM DD");

        });

        this.timeType = timeType;
        this.timeScale = 40; //px

        var iter_k = moment(this.firstDayDate).twix(this.lastDayDate).iterate(1, 'hours');

        var K_scale = 0;
        while (iter_k.hasNext()) {
            iter_k.next();
            K_scale = K_scale + 1;
        }

        K_scale = K_scale / div_hour;
        // var K_scale = hour2Range.length;
        //
        // var first_tzm_m = this.renderer.firstDayDate.format("ZZ");
        // var second_tzm_m = this.renderer.lastDayDate.format("ZZ");
        // var diff_tzm_h = ( first_tzm_m - second_tzm_m)/100;
        //
        // K_scale = K_scale - (diff_tzm_h / div_hour);


        this.timeline_width = this.timeScale * K_scale; // min otrzok 60 - eto 4 4asa. v sutkah 6 otrezkov
        // this.renderer.timeline_width = this.renderer.timeScale*1092.5; // min otrzok 60 - eto 4 4asa. v sutkah 6 otrezkov

        this.pxScaleUTC = Math.round(this.timeScaleUTC / this.timeline_width); // skolko vremeni v odnom px


        this.AddItemsData();


        this.AddTimeLineHead(this.timeScale, this.timeType, daysGroup, false );
        this.AddTimeLineData(this.timeScale, this.timeType, this.rows_to_gantt);

        this.AddTimeLineArrow(this.timeline_width);

        this.AddTimeLineGhost();

        this.AddTimeLineSummary();
        this.AddTimeLineFirst();



    },

    ZoomDaysClick: function() {

                this.firstDayDate = moment(this.GtimeStart).clone().startOf('month'); //Start month
        this.lastDayDate = moment(this.GtimeStop).clone().endOf('month'); //End
        this.timeScaleUTC = this.lastDayDate.valueOf() - this.firstDayDate.valueOf(); // raznica vremeni
        this.firstDayScale = this.firstDayDate.valueOf();

        var currentLocaleData = moment.localeData();

        //Get Days Range
        var iter = moment(this.firstDayDate).twix(this.lastDayDate).iterate("days");

        var dayRange=[];
        while(iter.hasNext()){
            dayRange.push(iter.next().toDate())
        }

        //Get Year - Month range
        var iter_first = moment(this.firstDayDate).twix(this.lastDayDate).iterate("month");

        var monthRange=[];
        while(iter_first.hasNext()){

            var mt_month = iter_first.next();
            var month = [];

            month['year'] =  mt_month.year();
            month['month'] =  currentLocaleData.months(mt_month);
            month['days'] =  mt_month.daysInMonth();

            monthRange.push(month)
        }

        this.timeScale = 24; //px
        this.timeType = 'month_day';
        this.timeline_width = this.timeScale*dayRange.length;
        this.pxScaleUTC = Math.round(this.timeScaleUTC / this.timeline_width); // skolko vremeni v odnom px

        this.AddItemsData();

        this.AddTimeLineHead(this.timeScale, this.timeType, monthRange, dayRange );
        this.AddTimeLineData(this.timeScale, this.timeType, this.rows_to_gantt);

        this.AddTimeLineArrow(this.timeline_width);
        this.AddTimeLineGhost();

        this.AddTimeLineSummary();
        this.AddTimeLineFirst();

    },

    ZoomMonthClick: function() {

        this.firstDayDate = moment(this.GtimeStart).clone().startOf('month'); //Start month
        this.lastDayDate = moment(this.GtimeStop).clone().endOf('month'); //End
        this.timeScaleUTC = this.lastDayDate.valueOf() - this.firstDayDate.valueOf(); // raznica vremeni
        this.firstDayScale = this.firstDayDate.valueOf();

        var iter = moment(this.firstDayDate).twix(this.lastDayDate).iterate('month');

        var month2Range=[];
        while(iter.hasNext()){

             month2Range.push(iter.next().toDate())

        }

        var monthGroup = _(month2Range).groupBy(function (month) {
             return moment(month).format("YYYY");

        });


        this.timeScale = 30 ;//px
        this.timeType = 'year_month';

        this.timeline_width = this.timeScale*month2Range.length; // min otrzok 60 - eto 4 4asa. v sutkah 6 otrezkov
        this.pxScaleUTC = Math.round(this.timeScaleUTC / this.timeline_width); // skolko vremeni v odnom px

        this.AddItemsData();

        this.AddTimeLineHead(this.timeScale, this.timeType, monthGroup, false );
        this.AddTimeLineData(this.timeScale, this.timeType, this.rows_to_gantt);

        this.AddTimeLineArrow(this.timeline_width);
        this.AddTimeLineGhost();

        this.AddTimeLineSummary();
        this.AddTimeLineFirst();

    },


    ZoomWeeksClick: function() {

        this.firstDayDate = moment(this.GtimeStart).clone().startOf('isoWeek'); //Start month
        this.lastDayDate = moment(this.GtimeStop).clone().endOf('isoWeek'); //End
        this.timeScaleUTC = this.lastDayDate.valueOf() - this.firstDayDate.valueOf(); // raznica vremeni
        this.firstDayScale = this.firstDayDate.valueOf();

        var iter = moment(this.firstDayDate).twix(this.lastDayDate).iterate('Week');

        var week2Range=[];
        while(iter.hasNext()){

             week2Range.push(iter.next().toDate())

        }

        var weeksGroup = _(week2Range).groupBy(function (week) {
             return moment(week).format("YYYY");

        });


        this.timeScale = 30 ;//px
        this.timeType = 'month_week';

        this.timeline_width = this.timeScale*week2Range.length; // min otrzok 60 - eto 4 4asa. v sutkah 6 otrezkov
        this.pxScaleUTC = Math.round(this.timeScaleUTC / this.timeline_width); // skolko vremeni v odnom px

        this.AddItemsData();

        this.AddTimeLineHead(this.timeScale, this.timeType, weeksGroup, false );
        this.AddTimeLineData(this.timeScale, this.timeType, this.rows_to_gantt);

        this.AddTimeLineArrow(this.timeline_width);
        this.AddTimeLineGhost();
        this.AddTimeLineSummary();
        this.AddTimeLineFirst();


    },


    ZoomQuarterClick: function() {


        this.firstDayDate = moment(this.GtimeStart).clone().startOf('Quarter'); //Start month
        this.lastDayDate = moment(this.GtimeStop).clone().endOf('Quarter'); //End
        this.timeScaleUTC = this.lastDayDate.valueOf() - this.firstDayDate.valueOf(); // raznica vremeni
        this.firstDayScale = this.firstDayDate.valueOf();


        var iter = moment(this.firstDayDate).twix(this.lastDayDate).iterate('Quarter');

        var quarter2Range=[];
        while(iter.hasNext()){

             quarter2Range.push(iter.next().toDate())

        }

        var quarterGroup = _(quarter2Range).groupBy(function (quarter) {
             return moment(quarter).format("YYYY");

        });


        this.timeScale = 80 ;//px
        this.timeType = 'quarter';

        this.timeline_width = this.timeScale*quarter2Range.length; // min otrzok 60 - eto 4 4asa. v sutkah 6 otrezkov
        this.pxScaleUTC = Math.round(this.timeScaleUTC / this.timeline_width); // skolko vremeni v odnom px

        this.AddItemsData();

        this.AddTimeLineHead(this.timeScale, this.timeType, quarterGroup, false );
        this.AddTimeLineData(this.timeScale, this.timeType, this.rows_to_gantt);

        this.AddTimeLineArrow(this.timeline_width);
        this.AddTimeLineGhost();
        this.AddTimeLineSummary();
        this.AddTimeLineFirst();


    },



//Gutter Movie

    GutterMouseDown: function(event){

        this.$el.delegate('.task-gantt', 'mouseup', this.proxy('GutterMouseUp'));
        this.$el.delegate('.task-gantt', 'mousemove', this.proxy('GutterMouseMove'));
        this.gutterClientX = event.clientX;
    },


    GutterMouseUp: function(event){

        this.$el.undelegate('.task-gantt', 'mouseup');
        this.$el.undelegate('.task-gantt', 'mousemove');
    },

    GutterMouseMove: function(event){

        var parentOffset = $('.task-gantt-gutter').parent().offset();
        var pxc = this.gutterOffsetX + (event.clientX - parentOffset.left);

        $('.task-gantt-list').width(pxc);
        $('.timeline-gantt-items').width(pxc);


        this.session.gantt = pxc;
        this.gutterOffsetSession = pxc;
    },


    GutterOver: function(event){

        $('.task-gantt-gutter').addClass("task-gantt-gutter-hover");
        $('.timeline-gantt-gutter').addClass("task-gantt-gutter-hover");


    },

    GutterOut: function(event){

        $('.task-gantt-gutter').removeClass("task-gantt-gutter-hover");
        $('.timeline-gantt-gutter').removeClass("task-gantt-gutter-hover");


    },



//Today Focus of Gantt Line Focus
    ClickToday: function (event) {

        var today = new Date();

        var toscale = this.TimeToScale(today.getTime());

        this.TimeToLeft = toscale;
        this.Focus_Gantt(toscale);

    },

    // Any can focus on BAR
    Focus_Gantt: function(task_start){

        var new_scroll = task_start - 500;

        if (new_scroll < 0) {
            new_scroll = 0
        }


        $('.timeline-gantt-head').animate({scrollLeft: new_scroll}, 1000);
        $('.task-gantt-timeline').animate({scrollLeft: new_scroll}, 1000);

        this.gantt_timeline_scroll_widget.scrollOffset(new_scroll);


        // var scale_width = $('.timeline-gantt-scroll-scale').width()-50;
        //
        // var x1 = $('.task-gantt-timeline').width();
        // var x2 = $('.task-gantt-timeline-data').width();
        // var  scroll_width = x2 - x1;
        //
        // var scale = scroll_width/(scale_width);
        //
        // var offset_left = (task_start-500) / scale;
        //
        // if (offset_left > scale_width){
        //
        //     offset_left = scale_width
        // }
        //
        // if (offset_left < 0){
        //
        //     offset_left = 0
        // }
        //
        //
        // $(".timeline-gantt-scroll-slider").offset({ left: offset_left  });



    },

    TimeToScale: function(time){

       if (time){

        return Math.round((time-this.firstDayScale) / this.pxScaleUTC);
    }

    },



// HandleHover

    HandleHoverOver: function(ev) {

        if (ev.target.allowRowHover)
        {

            // var rowsort = '#task-gantt-item-sorting-'+ev.target['data-id'];
            var rowdata = '#task-gantt-timeline-row-'+ev.target['data-id'];
            // var rowitem = '#task-gantt-item-'+ev.target['data-id'];

            var z_item = '.task-gantt-item-' + ev.target['data-id'];

            // $(rowsort).addClass("task-gantt-sorting-item-hover");

            $(rowdata).addClass("task-gantt-timeline-row-hover");
            // $(rowitem).addClass("task-gantt-item-hover");

            $(z_item).addClass("task-gantt-item-hover");

            var item_info = '#item-info-' + ev.target['data-id'];
            $(item_info).addClass("item-info-hover");

        }

    },


    HandleHoverOut: function(ev) {

        var item_info = '#item-info-' + ev.target['data-id'];
        $(item_info).removeClass("item-info-hover");

        // var rowsort = '#task-gantt-item-sorting-'+ev.target['data-id'];
        var rowdata = '#task-gantt-timeline-row-'+ev.target['data-id'];
        // var rowitem = '#task-gantt-item-'+ev.target['data-id'];

        var z_item = '.task-gantt-item-' + ev.target['data-id'];

        // $(rowsort).removeClass("task-gantt-sorting-item-hover");
        $(rowdata).removeClass("task-gantt-timeline-row-hover");
        // $(rowitem).removeClass("task-gantt-item-hover");

        $(z_item).removeClass("task-gantt-item-hover");

        // console.debug(ev);

    },

    // HandleHover
    _add_hover: function (ev) {

        var rowdata = '#task-gantt-timeline-row-' + ev.data['data_id'];
        $(rowdata).addClass("task-gantt-timeline-row-hover");

        var item_info = '#item-info-' + ev.data['data_id'];
        $(item_info).addClass("item-info-hover");


    },

    _remove_hover: function (ev) {

        var rowdata = '#task-gantt-timeline-row-' + ev.data['data_id'];
        $(rowdata).removeClass("task-gantt-timeline-row-hover");

        var item_info = '#item-info-' + ev.data['data_id'];
        $(item_info).removeClass("item-info-hover");

    },




});

core.view_registry.add('ganttaps', GanttContainer);

return GanttContainer;
});
