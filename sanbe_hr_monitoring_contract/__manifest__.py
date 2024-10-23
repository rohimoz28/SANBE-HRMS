# -*- coding: utf-8 -*-
{
    'name': "Sanbe HR Monitoring Contract",

    'summary': "Sanbe HR Monitoring Contract",

    'description': """
   Sanbe HR Monitoring Contract
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
    'depends': ['base', 'hr','base_territory','sanbe_employement_details'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/hr_monitoring_contract.xml',
    ],
    'assets': {
        'web.assets_backend': [
            "/sanbe_hr_monitoring_contract/static/src/js/hr_monitoring_controller.js",
        ],
        'web.assets_qweb': [
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "images": ["static/description/banner.png"],
}

