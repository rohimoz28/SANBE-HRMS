/** @odoo-module **/
import { registry } from "@web/core/registry";
import { evaluateBooleanExpr } from "@web/core/py_js/py";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { patch } from "@web/core/utils/patch";
import { SelectCreateDialog } from "@web/views/view_dialogs/select_create_dialog";
import { useOwnedDialogs, useService, useBus } from "@web/core/utils/hooks";
import { DomainSelector } from "@web/core/domain_selector/domain_selector";
import { Domain } from "@web/core/domain";
import { ListController } from "@web/views/list/list_controller";
import { unique } from "@web/core/utils/arrays";
import { useModelWithSampleData } from "@web/model/model";
import {
    Component,
    onMounted,
    onWillPatch,
    onWillStart,
    useEffect,
    useRef,
    useState,
    useSubEnv,
} from "@odoo/owl";
import { usePager } from "@web/search/pager_hook";
import { Pager } from "@web/core/pager/pager";
import { download } from "@web/core/network/download";
import { ExportDataDialog } from "@web/views/view_dialogs/export_data_dialog";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { ListRenderer } from "@web/views/list/list_renderer";
import { computeViewClassName } from "@web/views/utils";
import { ViewButton } from "@web/views/view_button/view_button";
import { SearchBar } from "@web/search/search_bar/search_bar";
import { useSearchBarToggler } from "@web/search/search_bar/search_bar_toggler";

patch(X2ManyField.prototype, {

    onInputKeyUp() {
//        const record = this.model.root
        var value = $(event.currentTarget).val().toLowerCase();
        $(".o_list_table tr:not(:lt(1))").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    },
    setup() {
        super.setup(...arguments);
        this.dialogService = useService("dialog");
        this.addDialog = useOwnedDialogs();
        this.action = useService("action");
        this.rpc = useService("rpc");
        this.optionalActiveFields = [];
        this.IdsData = this.props.record.data[this.props.name].currentIds;
        this.searchBarToggler = useSearchBarToggler();
        this.firstLoad = true;
    },
    async onDirectExportData() {
        await this.downloadExport(this.defaultExportList, false, "xlsx");
    },
    _open_search_wizard(){
        var self = this;
        const { fieldString, multiSelect, resModel } = this.list;
        const dynamicFilters = this.IdsData.length
            ? [
                  {
                      domain: [["id", 'in', this.IdsData]],
                  },
              ]
            : undefined;
        this.addDialog(SelectCreateDialog, {
            noCreate: true,
            multiSelect: false,
            resModel: resModel,
            dynamicFilters,
            context: self.props.context || {},
        });

    },
    async importRecords() {
        const { context } = this.list;
        const resModel = this.list.resModel;
        this.action.doAction({
            type: "ir.actions.client",
            tag: "import",
            params: { model: resModel, context },
        });
    },
    get defaultExportList() {
        const { archInfo } = this;
        return []
    },
    async onExportData() {
        const dialogProps = {
            context: this.props.context,
            defaultExportList: this.defaultExportList,
            download: this.downloadExport.bind(this),
            getExportedFields: this.getExportedFields.bind(this),
            root: this.list.model.root,
            list: this.list,
        };
        this.dialogService.add(ExportDataDialog, dialogProps);
    },
    async downloadExport(fields, import_compat, format) {
        let ids = false;
        if (!this.isDomainSelected) {
            const resIds = this.list.resIds;
            ids = resIds.length > 0 && resIds;
        }
        const exportedFields = fields.map((field) => ({
            name: field.name || field.id,
            label: field.label || field.string,
            store: field.store,
            type: field.field_type || field.type,
        }));
        if (import_compat) {
            exportedFields.unshift({
                name: "id",
                label: _t("External ID"),
            });
        }
        const domain =
            typeof this.props.domain === "function" ? this.props.domain() : this.props.domain;
        await download({
            data: {
                data: JSON.stringify({
                    import_compat,
                    context: this.props.context,
                    domain: domain,
                    fields: exportedFields,
                    groupby: this.list.model.root.groupBy,
                    ids,
                    model: this.list.resModel,
                }),
            },
            url: `/web/export/${format}`,
        });
    },
    async getExportedFields(model, import_compat, parentParams) {
        model = this.list.resModel;
        return await this.rpc("/web/export/get_fields", {
            ...parentParams,
            model,
            import_compat,
        });
    },

     async Print_excel_report(){
        var model = this.props.record.resModel
        var order = this.props.record.data.id
        var one2many = this.props.name
        var relation=this.activeField.relation
        var related_field = this.field.relation_field
        var action = {
                type: "ir.actions.report",
                report_type: "xlsx",
                report_name: 'Excel',
                report_file: "report.excel",
                context:{'model':relation,'id':order,'field':related_field},
        };
        return this.action.doAction(action);
    },

});



