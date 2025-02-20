from odoo import fields, models, tools, api, _
from datetime import datetime,timedelta

class HrEmployeeContractMonitoring(models.Model):
    _auto = False
    _name = 'hr.employee.contract.monitoring'
    _description = 'Employee Contract Monitoring'
    _order = 'time_limit, start_notice'

    id = fields.Integer('ID', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    employee_name = fields.Char('Employee Name', required=True)
    nik_employee = fields.Char('Employee NIK', required=True)
    nik_lama = fields.Char('Old NIK', required=True)
    employee_address = fields.Char('Address', required=True)
    status_employee = fields.Char(string='Employee Status', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)
    company_name = fields.Char('Company Name', required=True)
    branch_id = fields.Many2one('res.branch', string='Branch', required=True)
    branch_name = fields.Char('Branch Name', required=True)
    territory_id = fields.Many2one('res.territory', string='Territory', required=True)
    territory_name = fields.Char('Territory Name', required=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    department_name = fields.Char('Department Name', required=True)
    job_id = fields.Many2one('hr.job', string='Job', required=True)
    job_name = fields.Char('Job Name', required=True)
    contract_id = fields.Many2one('hr.contract', string='Contract', required=True)
    contract_name = fields.Char('Contract Name', required=True)
    contract_number = fields.Char('Contract Number', required=True)
    mobile_phone = fields.Char('Contact Number', required=True)
    date_start = fields.Date('Start Date', required=True)
    date_end = fields.Date('End Date', required=True)
    time_limit = fields.Integer('Time Limit (days)', required=True)
    notice_days = fields.Integer('Notice Days', required=True)
    start_notice = fields.Date('Start of Notice Period')
    rehire = fields.Boolean('Rehire', default=False)
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER (
                        ORDER BY time_limit, employee_id, date_end, contract_id
                    ) AS id,
                    employee_id,
                    mobile_phone,
                    nik_employee,
                    nik_lama,
                    employee_name,
                    status_employee,
                    employee_address,
                    company_id,
                    company_name,
                    branch_id,
                    branch_name,
                    territory_id,
                    territory_name,
                    department_id,
                    department_name,
                    job_id,
                    job_name,
                    contract_id,
                    contract_name,
                    contract_number,
                    date_start,
                    date_end,
                    time_limit,
                    notice_days,
                    start_notice,
                    rehire
                FROM 
                    (
                        SELECT
                            he.id AS employee_id,
                            he.name AS employee_name,
                            he.mobile_phone AS mobile_phone,
                            he.nik AS nik_employee,
                            coalesce(he.nik_lama,he.nik) AS nik_lama,
                            he.employee_type AS status_employee,
                            concat(he.private_street,' ',he.private_street2,' ',he.private_city)  AS employee_address,
                            rc.id AS company_id,
                            rc.name AS company_name,
                            rb.id AS branch_id,
                            rb.name AS branch_name,
                            rt.id AS territory_id,
                            rt.name AS territory_name,
                            hd.id AS department_id,
                            hd.name AS department_name,
                            hj.id AS job_id,
                            hj.name AS job_name,
                            hc2.id AS contract_id,
                            hc2.name AS contract_name,
                            hc2.number AS contract_number,
                            hc2.date_start AS date_start,
                            hc2.date_end AS date_end,
                            hc2.date_end - current_date AS time_limit,
                            hc2.notice_days,
                            hc2.date_end - (hc2.notice_days + 1) AS start_notice,
                            COALESCE(hel2.end_contract, FALSE) AS rehire
                        FROM
                            hr_employee he
                            INNER JOIN (
                                SELECT MAX(id) AS id, employee_id
                                FROM hr_contract
                                GROUP BY employee_id
                            ) hc ON hc.employee_id = he.id
                            LEFT JOIN hr_contract hc2 ON hc.id = hc2.id AND hc.employee_id = he.id
                            LEFT JOIN res_company rc ON hc2.company_id = rc.id
                            LEFT JOIN res_branch rb ON hc2.branch_id = rb.id
                            LEFT JOIN res_territory rt ON hc2.area = rt.id
                            LEFT JOIN hr_department hd ON hc2.department_id = hd.id
                            LEFT JOIN hr_job hj ON hc2.job_id = hj.id
                            LEFT JOIN (
                                SELECT MAX(hel.id) AS id, hel.employee_id
                                FROM hr_employment_log hel
                                GROUP BY hel.employee_id
                            ) hel ON hel.employee_id = he.id
                            LEFT JOIN hr_employment_log hel2 ON hel.id = hel2.id and hel2.employee_id = he.id
                        WHERE
                            hc2.active = TRUE
                            AND he.active = TRUE
                            AND hc2.date_end - current_date <= 45
                    ) AS emp
        )
        """ % (self._table, ))