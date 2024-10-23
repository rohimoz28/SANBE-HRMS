# -*- coding : utf-8 -*-
#################################################################################
# Author    => Albertus Restiyanto Pramayudha
# email     => xabre0010@gmail.com
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA
#################################################################################
{
    'name': "Sanbe HR Resignation",

    'summary': "Sanbe HR Resignation",

    'description': """
  Sanbe HR Resignation
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
    'depends': ['base', 'hr_resignation','base_territory','sanbe_hr_extended','sanbe_hr_employee_approval'],
    'data': [
        'security/hr_resignation_security.xml',
        'views/hr_resignation.xml',
        'reports/rpt_paklaring.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        "web.assets_backend": [
            "sanbe_hr_resignation/static/src/js/hr_resignation_search.js",
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "images": ["static/description/banner.png"],
}