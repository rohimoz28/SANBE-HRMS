from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class ReportOvertimeAttendanceXlsx(models.AbstractModel):
    _name = 'report.sanbe_hr_tms.report_ot_attendance_excel'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        try:
            # Logging context for debugging
            _logger.info(f"Context: {self.env.context}")
            
            if not lines:
                active_ids = self.env.context.get('active_ids', [])
                active_model = self.env.context.get('active_model', 'sb.overtime.attendance')
                
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
            sheet = workbook.add_worksheet("Rekap Overtime")
            sheet.merge_range('A1:M1', 'Rekap Overtime Attendance - HRMS', format_header)
            row = 1
            sheet.merge_range('A2:B2', 'Business Unit:', format_data)
            sheet.merge_range('C2:D2', lines[0].branch_id.name if lines and lines[0].branch_id else '', format_data)
            row += 1
            sheet.merge_range('A3:B3', 'Sub Department:', format_data)
            sheet.merge_range('C3:D3', lines[0].department_id.complete_name if lines and lines[0].department_id else '', format_data)
            row += 1
            sheet.merge_range('A4:B4', 'Period:', format_data)
            sheet.merge_range('C4:D4', lines[0].periode_id.name if lines and lines[0].periode_id else '', format_data)
            row += 1
            sorted_lines = sorted(lines, key=lambda l: l.req_date)
            req_date_from = sorted_lines[0].req_date.strftime('%Y-%m-%d') if sorted_lines[0].req_date else ''
            req_date_to = sorted_lines[-1].req_date.strftime('%Y-%m-%d') if sorted_lines[-1].req_date else ''
            
            sheet.merge_range('A5:B5', 'Request Date:', format_data)
            sheet.merge_range('C5:D5', f'{req_date_from} - {req_date_to}', format_data)
            row += 1

            # Buat list unique & sorted request number
            unique_requests = list(set(line.no_request for line in lines if line.no_request))
            sorted_requests = sorted(unique_requests)

            # Atur posisi awal
            start_row = row  # baris saat ini
            label_col = 0    # kolom A
            data_start_col = 2  # mulai dari kolom C
            max_cols = 3     # maksimal 3 per baris

            # Tulis label "Request Number:" di kolom A
            sheet.merge_range('A6:B6', 'Request Number:', format_data)

           # Tulis data ke kolom C, D, E dst per 3 item per baris
            row_offset = 0
            for i in range(0, len(sorted_requests), max_cols):
                chunk = sorted_requests[i:i+max_cols]
                for j, req in enumerate(chunk):
                    sheet.write(start_row + row_offset, data_start_col + j, req, format_data)

                # hanya tulis label di baris pertama
                if row_offset > 0:
                    sheet.write(start_row + row_offset, label_col, '', format_data)

                row_offset += 1

            # Geser row ke bawah kalau mau lanjut tulis data lain
            row = start_row + row_offset

            # Headers
            headers = [
                'No', 'Employee Name', 
                'NIK', 'Req Time Fr', 'Req Time To', 'App Time Fr', 
                'App Time To', 'Rel Time Fr', 'Rel Time To', 'Shuttle Car', 'Dine In', 'Meal Cash', 'Cancel?' #'State', 'Period' 
                # 'Total Delay', 'Total Times Delay'
            ]

            # col_widths= max(len(header) + 2 for header in headers)
            col_widths= [len(headers) for headers in headers]

            # Write headers
            header_row = row + 1
            for col, header in enumerate(headers):
                sheet.write(header_row, col, header, format_header)

            # Write data
            # row = 3
            row = header_row + 1
            if not lines:
                sheet.write(row, 0, 'Tidak ada data', format_data)
                return

            # Detailed logging
            _logger.info(f"Processing {len(lines)} lines")

            for index, obj in enumerate(lines.sorted(lambda o: o.no_request), 1):
                try:
                    # Safely get values with error handling
                    data_row = [
                        index,
                        # obj.branch_id.name or 'Tidak Diketahui', #BU
                        # obj.department_id.complete_name or 'Tidak Diketahui', #Department
                        # obj.no_request or 'Tidak Diketahui', #No Request
                        # obj.req_date.strftime('%Y-%m-%d') or 'Tidak Diketahui', #Tanggal Request
                        obj.employee_id.name or None, #Employee
                        obj.nik or None, #NIK
                        self.float_to_time(obj.req_time_fr) or 0, #Req Time FR
                        self.float_to_time(obj.req_time_to) or 0, #Req Time To
                        self.float_to_time(obj.approve_time_from) or 0, #Approve Time From
                        self.float_to_time(obj.approve_time_to) or 0, #Approve Time To
                        self.float_to_time(obj.rlz_time_fr) or 0, #Rel Time From
                        self.float_to_time(obj.rlz_time_to) or 0, #Rel TIme To
                        obj.is_shuttle_car,
                        obj.is_dine_in,
                        obj.is_meal_cash,
                        obj.is_cancel
                        # obj.state or None, #State
                        # obj.periode_id.name or None #Periode ID
                        # obj.delay_total or 0,
                        # obj.delay_count or 0
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

    def float_to_time(self, float_time):
        hours = int(float_time) 
        minutes = int((float_time - hours) * 60) 
        return '{:02d}:{:02d}'.format(hours, minutes)