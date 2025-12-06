# -*- coding : utf-8 -*-
#################################################################################
# Author    => Albertus Restiyanto Pramayudha
# email     => xabre0010@gmail.com
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA
#################################################################################


from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta

from datetime import date
import logging

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    state = fields.Selection([
        ('draft', "Draft"),
        ('req_approval', 'Request For Approval'),
        ('rejected', 'Rejected'),
        ('approved', 'Approved'),
        ('inactive', 'Inactive'),
        ('hold', 'Hold'),
    ],
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,store=True,
        default='draft')

    def request_for_approval(self):
        query = """ select contract_id from hr_employee where id = %s """
        self.env.cr.execute((query)%(str(self.id)))
        for distinct_records in self.env.cr.dictfetchall():
            contract = self.env['hr.contract'].browse(distinct_records['contract_id'])
            if contract or self.job_status != 'contract':
                return self.write({'state': 'req_approval'})
            else:
                raise UserError('Please Create Contract Employee')

    def action_reject(self):
        return self.write({'state': 'rejected'})

    def action_hold(self):
        return self.write({'state': 'hold'})

    def action_set_approved(self):
        query = """ select contract_id from hr_employee where id = %s """
        self.env.cr.execute((query)%(str(self.id)))
        for distinct_records in self.env.cr.dictfetchall():
            contract = self.env['hr.contract'].browse(distinct_records['contract_id'])
            if contract:
                return self.write({'state': 'approved'})
            else:
                raise UserError('Please Create Contract Employee')

    def action_approval(self):
        self.ensure_one()
        for data in self.env['hr.employee'].browse(self.ids):
            if data.nik:
                data_upload_attendance = self.env['data.upload.attendance'].sudo().search([
                    ('nik', '=', self.nik)
                ])

                if data_upload_attendance:
                    data_employee = {
                        'employee_id': data.id,
                        'nik': data.nik,
                        'area_id': data.area.id,
                        'branch_id': data.branch_id.id,
                        'state': 'register'
                    }
                    data_upload_attendance.write(data_employee)
        datalog = {'employee_id': self.id,
                   'service_type': 'NEWS',
                   'start_date': self.join_date,
                   'end_date': False,
                   'bisnis_unit': self.branch_id.id,
                   'department_id': self.department_id.id,
                   'job_title': self.job_id.name,
                   'job_status': self.job_status,
                   'emp_status': self.emp_status}
        self.env['hr.employment.log'].sudo().create(datalog)
        
        self.write({'state': 'approved'})
        
        try:
            self.env.cr.execute("CALL generate_cuti()")
            self.env.cr.commit()
            _logger.info("Stored procedure executed successfully")
        except Exception as e:
            _logger.error("Error calling stored procedure: %s", str(e))
            raise UserError("Error executing the function: %s" % str(e))
        
        return True

    def unlink(self):
        for record in self:
            adatrans = False
            mytrans = self.env['hr.employee.mutations'].sudo().search([('employee_id', '=', record.id)])
            if mytrans:
                adatrans = True
            myresig = self.env['hr.resignation'].sudo().search([('employee_id', '=', record.id)])
            if myresig:
                adatrans = True
            if record.state == 'draft':
                return super().unlink()
            else:
                if adatrans == True:
                    raise UserError('It cannot be deleted because there is already a transaction')
                else:
                    return super().unlink()
