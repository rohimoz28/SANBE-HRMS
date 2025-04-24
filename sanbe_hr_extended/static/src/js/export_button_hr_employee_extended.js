/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";


export class OdooOwlListController1 extends ListController {
    setup() {
        super.setup();
    }

    showHrEmployee() {
        // window.location.href = '/hr/employee/export/xlsx';
        this.actionService.doAction('sanbe_hr_extended.action_hr_employee_export_wizard');
    } 
}


export const OwlListController = {
    ...listView,
    Controller: OdooOwlListController1,
}

const viewRegistry = registry.category('views');
viewRegistry.add('owl_list_controller_hr_employee', OwlListController)