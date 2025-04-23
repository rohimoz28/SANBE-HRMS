from collections import defaultdict
from datetime import datetime
from odoo.http import request
from odoo import http
import xlsxwriter
import logging
import base64
import io

_logger = logging.getLogger(__name__)

class HrEmployeeExportController(http.Controller):

    @http.route('/hr/employee/export/xlsx', type='http', auth='user')
    def export_excel(self, department_id=None):
        # Dapatkan branch aktif dari user
        active_branch = request.env.user.branch_id

        # Log param yang diterima
        _logger.info(f"[EXPORT] Param department_id: {department_id}")
        _logger.info(f"[EXPORT] Active Branch: {active_branch.name} ({active_branch.id})")

        domain = [('branch_id', '=', active_branch.id)]
        if department_id:
            try:
                department_id_int = int(department_id)
                domain.append(('department_id', '=', department_id_int))
            except ValueError:
                _logger.warning(f"[EXPORT] Invalid department_id: {department_id}")

        _logger.info(f"[EXPORT] Search Domain: {domain}")


        # Filter karyawan berdasarkan branch
        employees = request.env['hr.employee'].sudo().search(domain)
        _logger.info(f"[EXPORT] Total Employees Ditemukan: {len(employees)}")

        # Buat file excel di memory
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        # Buat worksheet per department (sub-department)
        departments = employees.mapped('department_id')

        for department in departments:
            sheet = workbook.add_worksheet(department.name[:31])

            # Header kolom
            headers = [
                'Badges Number',
                'NIK',
                'Employee Name',
                'Job Title',
                'Coach',
                'Work Unit',
                'Employee P Group',
                'Job Status',
                'Employment Status',
                'Join Date',
                'Title',
                'Back Title',
                'Work Mobile',
                'Gender',
                'Religion',
                'Marital Status',
                'Date of Birth',
                'KPI Category',
                'Contract Date From',
                'Contract Date To',
                'Bank Account Number',
                'BPJS No',
                'Jamsostek',
                'Jemputan',
                'Attendee Premi',
                'OT',
                'Transport',
                'Meal',
                'Night Shift',
                'Night Shift Amount',
                'Resign Date',
            ]

            # Header row
            for col_num, header in enumerate(headers):
                sheet.write(0, col_num, header)

            dept_employees = employees.filtered(lambda e: e.department_id == department)

            for row_num, emp in enumerate(dept_employees, start=1):
                badge_nos = ', '.join(emp.badges_nos.mapped('name')) if emp.badges_nos else ''
                
                sheet.write(row_num, 0, badge_nos)
                sheet.write(row_num, 1, emp.nik or '')
                sheet.write(row_num, 2, emp.name or '')
                sheet.write(row_num, 3, emp.job_id.name if emp.job_id else '')
                sheet.write(row_num, 4, emp.coach_id.name if emp.coach_id else '')
                sheet.write(row_num, 5, emp.work_unit or '')
                sheet.write(row_num, 6, emp.employee_group1 or '')
                sheet.write(row_num, 7, emp.job_status or '')
                sheet.write(row_num, 8, emp.emp_status or '')
                sheet.write(row_num, 9, str(emp.join_date or ''))
                sheet.write(row_num, 10, emp.title or '')
                sheet.write(row_num, 11, emp.back_title or '')
                sheet.write(row_num, 12, emp.mobile_phone or '')
                sheet.write(row_num, 13, emp.gender or '')
                sheet.write(row_num, 14, emp.religion or '')
                sheet.write(row_num, 15, emp.marital or '')
                sheet.write(row_num, 16, str(emp.birthday or ''))
                sheet.write(row_num, 17, emp.kpi_kategory or '')
                sheet.write(row_num, 18, str(emp.contract_datefrom or ''))
                sheet.write(row_num, 19, str(emp.contract_dateto or ''))
                sheet.write(row_num, 20, emp.bank_account_id.acc_number if emp.bank_account_id else '')
                sheet.write(row_num, 21, emp.insurance or '')
                sheet.write(row_num, 22, emp.jamsostek or '')
                sheet.write(row_num, 23, emp.allowance_jemputan or '')
                sheet.write(row_num, 24, emp.attende_premie or '')
                sheet.write(row_num, 25, emp.allowance_ot or '')
                sheet.write(row_num, 26, emp.allowance_transport or '')
                sheet.write(row_num, 27, emp.allowance_meal or '')
                sheet.write(row_num, 28, emp.allowance_night_shift or '')
                sheet.write(row_num, 29, emp.allowance_nightshift_amount or '')
                sheet.write(row_num, 30, str(emp.resign_date or ''))


        # Tutup workbook dan kirim file ke user
        workbook.close()
        output.seek(0)
        excel_data = output.read()

        # Nama file dinamis berdasarkan branch
        filename = f"rekap_karyawan_{active_branch.name.replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

        return request.make_response(
            excel_data,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                (f'Content-Disposition', f'attachment; filename={filename}')
            ]
        )
