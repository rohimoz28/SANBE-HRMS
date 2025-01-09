from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging
_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    """Extended model for HR employees with additional features."""
    _inherit = 'hr.employee'

    ptkp = fields.Selection(selection=[('TK0', "TK0"),
                                        ('TK1', "TK1"),
                                        ('TK2', "TK2"),
                                        ('TK3', "TK3"),
                                        ('K0', "K0"),
                                        ('K1', "K1"),
                                        ('K2', "K2"),
                                        ('K3', "K3"),],
                                    string="PTKP", default='TK0')

    _sql_constraints = [
        # ('nik_uniq', 'check(1=1)', "The NIK  must be unique, this one is already assigned to another employee."),
        # ('no_ktp_uniq', 'check(1=1)', "The NO KTP  must be unique, this one is already assigned to another employee."),
        # ('no_npwp_uniq', 'check(1=1)',
        #  "The NO NPWP  must be unique, this one is already assigned to another employee."),
        # ('identification_id_uniq', 'check(1=1)',
        #  "The Identification ID  must be unique, this one is already assigned to another employee."),
        ('contract_id_unique', 'UNIQUE(contract_id)', "Contract must be unique, this one is already assigned to another employee."),
    ]
    
