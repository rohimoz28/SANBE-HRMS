/** @odoo-module */

import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";

export class MonitorOvertimeController extends ListController {
    setup() {
        super.setup();
    }

    showMonitorOvertime() {
    this.env.services.action.doAction({
        type: 'ir.actions.act_window',
        name: 'Monitor Overtime',
        res_model: 'export.excel.monitor.ot',
        view_mode: 'tree',
        view_id: 'sanbe_hr_tms.export_excel_monitor_ot_action_wizard',
        views: [[false, 'form']],
        target: 'new'
    });
   }
}

const viewRegistry = registry.category("views");
export const MonitorOTController = {
    ...listView,
    Controller: MonitorOvertimeController,
};
viewRegistry.add("owl_list_controller_monitor_ot", MonitorOTController)