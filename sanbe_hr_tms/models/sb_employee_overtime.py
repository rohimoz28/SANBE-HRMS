from odoo import fields, models, api

class SbEmployeeOvertime(models.Model):
    _name = 'sb.employee.overtime'
    _description = 'For Monitoring Employee Overtime'

    area_id = fields.Many2one('res.territory', string='Area')
    branch_id = fields.Many2one('res.branch', string='Unit')
    department_id = fields.Many2one('hr.department', string='Department')
    nik = fields.Char('NIK')
    employee_id = fields.Many2one('hr.employee', string='Nama')
    attendee_total = fields.Integer('Jumlah Hari Hadir')
    job_id = fields.Many2one('hr.job', string='Jabatan')
    net_salary = fields.Float('Net Salary')
    pharma_allowance = fields.Float('Tunj. Kefarmasian')
    work_allowance = fields.Float('Tunj. Masa Kerja')
    family_allowance = fields.Float('Tunj. Keluarga')
    salary_total = fields.Float('Total Gaji')
    aot1 = fields.Float('Jam Lembur 1')
    aot2 = fields.Float('Jam Lembur 2')
    aot3 = fields.Float('Jam Lembur 3')
    aot4 = fields.Float('Jam Lembur 4')
    rp_aot1 = fields.Float('Jam Lembur 1')
    rp_aot2 = fields.Float('Jam Lembur 2')
    rp_aot3 = fields.Float('Jam Lembur 3')
    rp_aot4 = fields.Float('Jam Lembur 4')
    aot_total = fields.Float('Total Lembur')
    salary_allowance_total = fields.Float('Gaji + Tunjangan + Lembur', 
                                          help='TOTAL NET + TUNJ KEFARMASIAN + TMK + TUN KEL+ LEMBUR')
    aot_salary_percentage = fields.Float('% Lembur vs Total Gaji', 
                                         help='% LEMBUR / NET+TUNJ KEFARMASIAN + TMK + TUNJ KEL')


