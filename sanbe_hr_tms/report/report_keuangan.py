from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class ReportKehadiranXlsx(models.AbstractModel):
    _name = 'report.sanbe_hr_tms.rekap_keuangan_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        try:
            # Logging context for debugging
            _logger.info(f"Context: {self.env.context}")
            
            if not lines:
                active_ids = self.env.context.get('active_ids', [])
                active_model = self.env.context.get('active_model', 'hr.tmsentry.summary')
                
                lines = self.env[active_model].browse(active_ids) if active_ids else []
            
            # Log total 
            _logger.info(f"Total lines retrieved: {len(lines)}")

            # Formatting
            format_header = workbook.add_format({
                'font_size': 11,
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
            sheet = workbook.add_worksheet("Rekap Kehadiran")
            sheet.merge_range('A1:AT1', 'Rekap Perhitungan Kehadiran dan Overtime - HRMS', format_header)

            # Headers
            headers = [
                'No',
                'FKELOMPOK',
                'FBAGIAN',
                'FSALARY_KE',
                'FNIK',
                'FNAMA',
                'FSP',
                'FMASAKRJ',
                'FSTATUS',
                'FNPWP',
                'FTANGGUNG',
                'FKONTRAK',
                'FHRNORMAL',
                'FHARIBYR',
                'FHADIR',
                'FHARILMB',
                'FDINAS1',
                'FDINAS2',
                'FLEMBUR1',
                'FLEMBUR2',
                'FLEMBUR3',
                'FLEMBUR4',
                'FSAKIT',
                'FIJIN',
                'FSUKA',
                'FCCLKOP',
                'FBUNGA',
                'FHTRANS',
                'FHMAKAN',
                'FCUTIHML',
                'FCUTIBYR',
                'FKOPERASI',
                'FCCLBAKO',
                'FTJBBM',
                'FTRPSP',
                'FINCENTIVE',
                'FTJMK',
                'FTJKEL',
                'FUPSH',
                'FBFFLAG001',
                'FCUTITHN',
                'FLMBBI',
                'FLMBBS',
                'FLEVEL_JAB',
                'FJOB_TITLE',
                'FKPI_CTCGRY'
            ]

            # col_widths= max(len(header) + 2 for header in headers)
            col_widths= [len(headers) for headers in headers]

            # Write headers
            for col, header in enumerate(headers):
                sheet.write(2, col, header, format_header)

            # Write data
            row = 3
            if not lines:
                sheet.write(row, 0, 'Tidak ada data', format_data)
                return

            # Detailed logging
            _logger.info(f"Processing {len(lines)} lines")

            for index, obj in enumerate(lines, 1):
                try:
                    # Safely get values with error handling
                    data_row = [
                        index,                                      # 1. No
                        None,                                       # 2. Kelompok
                        None,                                       # 3. Bagian
                        None,                                       # 4. Salary ke
                        obj.nik or None,                            # 5. NIK
                        obj.employee_id.name if obj.employee_id else None,  # 6. Nama Karyawan
                        None,                                       # 7. SP
                        None,                                       # 8. Masa Kerja
                        None,                                       # 9. Status
                        obj.employee_id.no_npwp or None,            # 10. NPWP
                        None,                                       # 11. Tanggungan
                        None,                                       # 12. Kontrak ke
                        obj.employee_id.workingday or 0,            # 13. Hari Normal
                        (obj.attendee_count or 0) 
                            + (obj.leave_count or 0) 
                            + (obj.sick_count or 0),                # 14. Hari Bayar (hadir+izin+sakit)
                        obj.attendee_count or 0,                    # 15. Hadir
                        len(obj.tmsentry_details_30_ids),           # 16. Hari Lembur
                        obj.nightshift_count or 0,                  # 17. Dinas 1
                        obj.nightshift2_count or 0,                 # 18. Dinas 2
                        obj.ot1_totalx or 0,                        # 19. Lembur 1
                        obj.ot2_totalx or 0,                        # 20. Lembur 2
                        obj.ot3_totalx or 0,                        # 21. Lembur 3
                        obj.ot4_totalx or 0,                        # 22. Lembur 4
                        obj.sick_count or 0,                        # 23. Sakit
                        obj.leave_count or 0,                       # 24. Izin
                        None,                                       # 25. Suka
                        None,                                       # 26. CCL Koperasi
                        None,                                       # 27. Bunga
                        None,                                       # 28. Htrans
                        None,                                       # 29. Hmakan
                        None,                                       # 30. Cuti hamil
                        None,                                       # 31. Cuti bayar
                        None,                                       # 32. Koperasi
                        None,                                       # 33. CCL bako
                        None,                                       # 34. Tj BBM
                        None,                                       # 35. Trp SP
                        None,                                       # 36. Incentive
                        None,                                       # 37. Tj MK
                        None,                                       # 38. Tj Keluarga
                        None,                                       # 39. UPSH
                        None,                                       # 40. Flag 001
                        None,                                       # 41. Cuti tahunan
                        None,                                       # 42. Lembur BI
                        None,                                       # 43. Lembur BS
                        obj.employee_id.employee_levels.name if obj.employee_id else None, # 44. Level Jab
                        obj.employee_id.job_id.name if obj.employee_id else None,          # 45 Job Title
                        None,                                       # 46 KPI Category
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
            