{
    'name': "Sanbe HR Installment",

    'summary': "Sanbe HR Installment",

    'description': """
        Sanbe HR Installment
    """,

    'author': "Sanbe IT Corp",
    'website': "http://www.yourcompany.com",
    "support": "info@sanbe-farma.com",
    'category': 'Tools',
    'version': '0.1',
    'license': 'LGPL-3',
    'price': 0,
    'currency': 'USD',

    # any module necessary for this one to work correctly
    # 'depends': ['base', 'sanbe_hr_tms','hr_payroll_community', 'sanbe_hr_extended'],
    'depends': ['base', 'hr','base_territory', 'sanbe_hr_extended'],
    'data': [
        # 'views/hr_emp_status.xml',
        'security/installment_groups.xml',
        'security/ir.model.access.csv',
        'security/config_parameter.xml',
        'security/installment_branch_security.xml',
        'views/sb_loan_installment.xml',
        'views/sb_loan_installment_monitoring.xml',
        'views/hr_installment_menu.xml'
    ],
    'assets': {
        'web.assets_backend': [
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "images": ["static/description/banner.png"],
}

