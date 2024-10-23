# -*- coding : utf-8 -*-
#################################################################################
# Author    => Albertus Restiyanto Pramayudha
# email     => xabre0010@gmail.com
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA
#################################################################################
{
    'name': "Sanbe HR TMS",
    'summary': "Sanbe HR TMS",
    'description': """
            Sanbe HR TMS
    """,
    'author': "Albertus Restiyanto Pramayudha",
    'website': "http://www.yourcompany.com",
    "support": "xabre0010@gmail.com",
    'category': 'Human Resource',
    'version': '0.1',
    'license': 'LGPL-3',
    'price': 0,
    'currency': 'USD',
    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_holidays','sanbe_hr_employee_mutation','hr_attendance','hr_holidays_attendance','base_territory','project','sale','purchase','stock','account','event','field_timepicker'],
    'data': [
        'views/hr_disable_others.xml',
        'views/hr_public_holiday.xml',
        'views/hr_workingday_setting.xml',
        'views/hr_empgroup_settings.xml',
        'views/hr_permission_entry.xml',
        'views/hr_tmsentry_summary.xml',
        'views/hr_tms_recapitulation.xml',
        'views/hr_tms_sync_machine.xml',
        'views/hr_tms_processing.xml',
        'views/hr_overtime_request_planning.xml',
        'views/tms_entry.xml',
        'views/hr_tms_open_close.xml',
        'views/hr_tms_machine_setting.xml',
        'wizards/cari_employee_department.xml',
        'wizards/hr_tmsimport_data_entry.xml',
        'wizards/hr_list_employee_scheduled.xml',
        'views/hr_transfer_to_payroll.xml',
        'views/hr_employee.xml',
        'security/ir.model.access.csv',
        'security/tms_branch_security.xml',
        # 'views/tms_menu.xml',
        'data/tms_seq_number.xml'
    ],
    'assets': {
            'web.assets_backend': [
                'hr_holidays/static/src/**/*',
            ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "images": ["static/description/banner.png"],
}