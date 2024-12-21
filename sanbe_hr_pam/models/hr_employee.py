from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging
_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    """Extended model for HR employees with additional features."""
    _inherit = 'hr.employee'

    _sql_constraints = [
        # ('nik_uniq', 'check(1=1)', "The NIK  must be unique, this one is already assigned to another employee."),
        # ('no_ktp_uniq', 'check(1=1)', "The NO KTP  must be unique, this one is already assigned to another employee."),
        # ('no_npwp_uniq', 'check(1=1)',
        #  "The NO NPWP  must be unique, this one is already assigned to another employee."),
        # ('identification_id_uniq', 'check(1=1)',
        #  "The Identification ID  must be unique, this one is already assigned to another employee."),
        ('contract_id_unique', 'UNIQUE(contract_id)', "Contract must be unique, this one is already assigned to another employee."),
    ]
    
