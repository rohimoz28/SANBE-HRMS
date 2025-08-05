/** @odoo-module */

import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";

export class EocOdooOWLListController extends ListController {
   setup() {
       super.setup();
   }

   showEOC() {
    this.env.services.action.doAction({
        type: 'ir.actions.act_window',
        name: 'EOC Report',
        res_model: 'hr.eoc.report',
        view_mode: 'tree',
        view_id: 'sanbe_hr_monitoring_contract.hr_eoc_report_action_wizard',
        views: [[false, 'form']],
        target: 'new'
    });
   }
}


const viewRegistry = registry.category("views");
export const EocWizardController = {
    ...listView,
    Controller: EocOdooOWLListController,
};
viewRegistry.add("owl_list_controller_eoc_wizard", EocWizardController);