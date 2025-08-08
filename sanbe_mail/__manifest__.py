# -*- coding: utf-8 -*-
{
    'name': 'Sanbe Farma Mail',
    'version': '17.0.1.0.0',
    'summary': 'Emails, templates, and scheduled notifications for Sanbe Farma',
    'description': """
        Sanbe Farma Mail Configuration 
        ===========================
        Custom mail module for Sanbe Farma. Integrates with mail.mail, mail.template, and ir.cron to:
        - Send templated emails automatically
        - Schedule periodic reports or reminders
        - Handle internal email workflows
    """,
    'category': 'Communication',
    'author': 'IT Corporate Team',
    'website': 'https://www.sanbe-farma.com/',
    'price': 0,
    'currency': 'USD',
    'depends': ['base', 'mail','base_territory'],
    "data": [
        "security/group.xml",
        "security/ir.model.access.csv",
        "data/sanbe_mail_scheduler_cron.xml",
        "views/sanbe_global_setting.xml",
        "views/sanbe_mail_config_views.xml",
        "views/sanbe_mail_template_views.xml"
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
