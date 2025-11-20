import io
import base64
from odoo import _, api, fields, models
from odoo.exceptions import UserError
import xlsxwriter
import logging
_logger = logging.getLogger(__name__)

class ExportExcelOvertimeAttendance(models.TransientModel):
    _name = 'export.excel.ot.attendance'
    # _inherit = 'hr.tmsentry.summary'
    _description = 'Export Excel Overtime Request'

    branch_id = fields.Many2one(
        'res.branch', 
        string='Business Unit',
        domain=lambda self: self._get_branches_domain(),
        options="{'no_create': True}"
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Sub Department',
        # domain=lambda self: self._get_departments_domain(),
        domain="[('id', 'in', department_ids)]",
        options="{'no_create': True}"
    )
    department_ids = fields.Many2many(
        'hr.department',
        compute='_compute_department_ids',
        store=False
    )
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    ot_request_id = fields.Many2one(
        'hr.overtime.planning',
        string='OT Request',
        domain = "[('department_id', '=', department_id)]"
        
    )

    # def _get_departments_domain(self):
    #     """
    #     Return the domain to filter departments based on the departments
    #     available in the sb.overtime.attendance model.
    #     """
    #     department_ids = self.env['sb.overtime.attendance'].search([('branch_id','=',self.branch_id.id)]).mapped('department_id.id')
    #     return [('id', 'in', department_ids)]
    
    def _get_branches_domain(self):
        """
        Return domain untuk branch_id berdasarkan branch_id yang ada di model sb.overtime.attendance.
        """
        branch_ids = self.env['sb.overtime.attendance'].search([]).mapped('branch_id.id')
        return [('id', 'in', branch_ids)]
    
    @api.depends('branch_id')
    def _compute_department_ids(self):
        """
        Compute field department_ids berdasarkan branch_id yang dipilih dan department_id yang ada di model sb.overtime.attendance.
        Field department_ids digunakan sebagai domain untuk department_id.
        """
        for rec in self:
            if rec.branch_id:
                dept_ids = self.env['sb.overtime.attendance'].search([
                    ('branch_id', '=', rec.branch_id.id)
                ]).mapped('department_id').ids
            else:
                dept_ids = []

            rec.department_ids = [(6, 0, dept_ids)]
    
    def button_export_html(self):
        self.ensure_one()
        
        ot_attendance_domain = []
        if self.branch_id:
            ot_attendance_domain.append(('branch_id', '=', self.branch_id.id))
        if self.department_id:
            ot_attendance_domain.append(('department_id', '=', self.department_id.id))
        if self.start_date:
            ot_attendance_domain.append(('req_date', '>=', self.start_date))
        if self.end_date:
            ot_attendance_domain.append(('req_date', '<=', self.end_date))
        if self.ot_request_id:
            ot_attendance_domain.append(('no_request', '=', self.ot_request_id.name))

        ot_attendance = self.env['sb.overtime.attendance'].search(ot_attendance_domain)
        
        if not ot_attendance:
            raise UserError(_("Tidak Ada Data Record Dari department yang dipilih"))
        
        return {
            'type': 'ir.actions.report',
            'report_name': 'sanbe_hr_tms.report_ot_attendance_html',
            'report_type': 'qweb-html',
            'report_file': f'Rekap_Overtime_{self.department_id.complete_name or "All"}',
            'context': {
                'active_model': 'sb.overtime.attendance',
                'active_ids': ot_attendance.ids,  # semua record
            }
        }

    def button_export_xlsx(self):
        self.ensure_one()
        
        ot_attendance_domain = []
        if self.branch_id:
            ot_attendance_domain.append(('branch_id', '=', self.branch_id.id))
        if self.department_id:
            ot_attendance_domain.append(('department_id', '=', self.department_id.id))
        if self.start_date:
            ot_attendance_domain.append(('req_date', '>=', self.start_date))
        if self.end_date:
            ot_attendance_domain.append(('req_date', '<=', self.end_date))
        if self.ot_request_id:
            ot_attendance_domain.append(('no_request', '=', self.ot_request_id.name))

        ot_attendance = self.env['sb.overtime.attendance'].search(ot_attendance_domain)
        
        if not ot_attendance:
            raise UserError(_("Tidak Ada Data Record Dari department yang dipilih"))
        
        return {
            'type': 'ir.actions.report',
            'report_name': 'sanbe_hr_tms.report_ot_attendance_excel',
            'report_type': 'xlsx',
            'report_file': f'Rekap_Overtime_{self.department_id.complete_name or "All"}',
            'context': {
                'active_model': 'sb.overtime.attendance',
                'active_ids': ot_attendance.ids,  # semua record
            }
        }