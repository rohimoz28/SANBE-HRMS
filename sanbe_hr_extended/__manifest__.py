# -*- coding : utf-8 -*-
#################################################################################
# Author    => Albertus Restiyanto Pramayudha
# email     => xabre0010@gmail.com
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA
#################################################################################

{
    'name': "Sanbe HR Extended",

    'summary': "Sanbe HR Extended",

    'description': """
   Sanbe HR Extended
    """,

    'author': "Albertus Restiyanto Pramayudha",
    'website': "http://www.yourcompany.com",
    "support": "xabre0010@gmail.com",
    'category': 'Tools',
    'version': '0.1',
    'license': 'LGPL-3',
    'price': 0,
    'currency': 'USD',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr','sanbe_hr','hr_payroll_community','hr_contract'],
    'data': [
        'security/hr_branch_security.xml',
        'security/ir.model.access.csv',
        'views/hr_employee.xml',
        'views/employee_level.xml',
        'data/hitung_employee_ws.xml',
        'data/sequence_employee_id.xml',
        'data/email_contract_notification.xml',
        'views/hr_contracts.xml',
        'views/hr_department.xml',
        'views/hr_contract_type.xml',
        'views/hr_pension_monitoring.xml',
        'views/hr_approval_setting.xml',

        'wizards/hr_employee_wizard.xml',
        'wizards/employee_report_wizard.xml',

        'controllers/employee_report_html.xml',
        'controllers/employee_report_excel.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sanbe_hr_extended/static/src/xml/export_button_hr_employee_extended.xml',
            'sanbe_hr_extended/static/src/js/export_button_hr_employee_extended.js',
            'sanbe_hr_extended/static/src/css/hide_search_panel.css',
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "images": ["static/description/banner.png"],
}

