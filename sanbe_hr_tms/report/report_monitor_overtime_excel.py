from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class ReportMonitorOvertimeXlsx(models.AbstractModel):
    _name = 'report.sanbe_hr_tms.report_monitor_overtime_excel'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        try:
            # Logging context for debugging
            _logger.info(f"Context: {self.env.context}")
            
            if not lines:
                active_ids = self.env.context.get('active_ids', [])
                active_model = self.env.context.get('active_model', 'sb.employee.overtime')
                
                lines = self.env[active_model].browse(active_ids) if active_ids else []
            
            # Log total 
            _logger.info(f"Total lines retrieved: {len(lines)}")

            # Formatting
            format_header = workbook.add_format({
                'font_size': 14,
                'bold': True,
                'align': 'center',
                'bg_color': '#F2F2F2',
                'border': 1
            })

            format_data = workbook.add_format({
                'font_size': 12,
                'align': 'left',
                'valign': 'vcenter'
            })

            # Create worksheet
            sheet = workbook.add_worksheet("Report Monitoring Overtime")
            sheet.merge_range('A2:W2', 'LEMBAR LAPORAN PENGAWASAN DAN EVALUASI BIAYA GAJI DAN LEMBUR KARYAWAN/BURUH', format_header)
            sheet.merge_range('A3:C3', 'PERIODE SALARY BULAN', format_data)
            sheet.merge_range('A4:C4', 'PERIODE HARI LEMBUR', format_data)
            sheet.merge_range('M6:P6', 'JAM LEMBUR', format_header)
            sheet.merge_range('Q6:U6', 'Rp LEMBUR', format_header)

            # Headers
            headers = [
                'No', 'UNIT', 'DEPARTMENT', 'NIK', 'NAMA', 'JUMLAH HARI HADIR', 'JABATAN', 'NET SALARY',
                'TUNJ.KEFARMASIAN', 'TUNJ MASA KERJA (TMK)', 'TUNJ KELUARGA', 'TOTAL GAJI', 'Lem. 1', 'Lem.2',
                'Lem.3', 'Lem.4', 'Rp Lembur 1', 'Rp Lembur 2', 'Rp Lembur 3', 'Rp Lembur 4', 'TOTAL LEMBUR (Rp)',
                'TOTAL NET + TUNJ KEFARMASIAN + TMK + TUN KEL+ LEMBUR', '%LEMBUR / NET+TUNJ KEFARMASIAN + TMK + TUNJ KEL'
            ]

            # col_widths= max(len(header) + 2 for header in headers)
            col_widths= [len(headers) for headers in headers]

            # Write headers
            for col, header in enumerate(headers):
                sheet.write(6, col, header, format_header)
            
            # Write data
            row = 7
            if not lines:
                sheet.write(row, 0, 'Tidak ada data', format_data)
                return

            # Detailed logging
            _logger.info(f"Processing {len(lines)} lines")

            for index, obj in enumerate(lines.sorted(lambda o: o.employee_id.name), 1):
                try:
                    # Safely get values with error handling
                    data_row = [
                        index,
                        obj.branch_id.name,
                        obj.department_id.complete_name,
                        obj.nik,
                        obj.employee_id.name,
                        obj.attendee_total,
                        obj.job_id.name,
                        obj.net_salary,
                        obj.pharma_allowance,
                        obj.work_allowance,
                        obj.family_allowance,
                        obj.salary_total,
                        obj.aot1,
                        obj.aot2,
                        obj.aot3,
                        obj.aot4,
                        obj.rp_aot1,
                        obj.rp_aot2,
                        obj.rp_aot3,
                        obj.rp_aot4,
                        obj.aot_total,
                        obj.salary_allowance_total,
                        obj.aot_salary_percentage
                    ]

                    # Logging each row for detailed debugging
                    _logger.info(f"Processing row {index}: {data_row}")

                    # Write row data and update column widths
                    for col, value in enumerate(data_row):
                        str_value = str(value)
                        sheet.write(row, col, value, format_data)
                        
                        # Update column width if needed
                        col_widths[col] = max(col_widths[col], len(str_value) + 2)

                    row += 1

                except Exception as row_error:
                    _logger.error(f"Error processing row {index}: {row_error}")
            
            # Set column widths
            for col, width in enumerate(col_widths):
                sheet.set_column(col, col, min(width, 50))

        except Exception as e:
            _logger.error(f"Critical error in generate_xlsx_report: {e}")
