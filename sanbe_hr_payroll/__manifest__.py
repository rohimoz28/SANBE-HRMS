# -*- coding : utf-8 -*-
#################################################################################
# Author    => Albertus Restiyanto Pramayudha
# email     => xabre0010@gmail.com
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA
#################################################################################
{
    'name': "Sanbe HR Payroll",
    'summary': "Sanbe HR Payroll",
    'description': """
            Sanbe HR Payroll
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
    'depends': ['base', 'sanbe_hr_tms','hr_payroll_community'],
    'data': [
        'views/hr_payroll_entry.xml',
        'views/hr_payroll_menu.xml',
        'security/ir.model.access.csv',
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