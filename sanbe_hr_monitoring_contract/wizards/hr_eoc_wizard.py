import io
import base64
from odoo import _, api, fields, models
from odoo.exceptions import UserError
import xlsxwriter
import logging
_logger = logging.getLogger(__name__)

class HrEocReport(models.TransientModel):
    _name = 'hr.eoc.report'
    _description = 'End Of Contract Report'

    name = fields.Char('Nomor')
    department_id = fields.Many2one('hr.department', string='Department', domain=lambda self: self._get_department_ids())
    parent_id = fields.Many2one('hr.employee', string='Tujuan', domain=lambda self: self._get_parent_ids())

    @api.model
    def _get_parent_ids(self):
        parent_ids = self.env['hr.employee.contract.monitoring'].search([]).mapped('coach_id.id')
        _logger.info("Parent_ids: ", parent_ids)
        return [('id', 'in', parent_ids)]
    
    def _get_department_ids(self):
        department_ids = self.env['hr.employee.contract.monitoring'].search([]).mapped('department_id.id')
        _logger.info("department_ids: ", department_ids)
        return [('id', 'in', department_ids)]

    def button_export_pdf(self):
        return self.env.ref('sanbe_hr_monitoring_contract.hr_eoc_report_action').report_action(self)

    
    # def button_export_pdf(self):
    #     self.ensure_one()
        
    #     eoc_domain = []

    #     if self.department_id:
    #         eoc_domain.append(('department_id', '=', self.department_id.id))
    #     if self.parent_id:
    #         eoc_domain.append(('coach_id', '=', self.parent_id.id))

    #     eoc_report = self.env['hr.employee.contract.monitoring'].search(eoc_domain)

    #     return {
    #         'type': 'ir.actions.report',
    #         'report_name': 'sanbe_hr_monitoring_contract.hr_eoc_report_template',
    #         'report_type': 'qweb-pdf',
    #         'report_file': f'Report_EOC_{self.parent_id.name or "All"}',
    #         'context': {
                # 'active_model': 'hr.employee.contract.monitoring',
                # 'active_ids': eoc_report.ids,

        #         'active_model': 'hr.eoc.report',
        #         'active_ids': [self.id],
        #         'eoc_report_ids': eoc_report.ids,
        #     }
        # }

        # return self.env.ref('sanbe_hr_monitoring_contract.hr_eoc_report_action').report_action(self)
