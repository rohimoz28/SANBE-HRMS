# -*- coding: utf-8 -*-
import re
import html
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import html_sanitize

class SANBEMailTemplate(models.Model):
    _name = 'sanbe.mail.template'
    _description = 'SANBE Mail Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Template Name', required=True, tracking=True)
    code = fields.Char(string='Template Code', required=True, tracking=True)
    subject = fields.Char(string='Subject', required=True, tracking=True)

    company_id = fields.Many2one('res.company', string='Company', tracking=True)
    branch_id = fields.Many2one('res.branch', string='Branch', tracking=True)

    email_to = fields.Text(string='To (Email)', required=True, tracking=True)
    email_cc = fields.Text(string='CC', tracking=True)
    description = fields.Text(string='Description', tracking=True)

    header_template = fields.Text(string='Header Template', help="Content shown at the top of the email.", tracking=True)
    bottom_template = fields.Text(string='Bottom Template', help="Content shown at the bottom of the email.", tracking=True)

    header_templates_html = fields.Html(string='Header Template HTML', store=True, help="HTML content for email header.")
    bottom_templates_html = fields.Html(string='Bottom Template HTML', store=True, help="HTML content for email footer.")

    model_id = fields.Many2one('ir.model', string='Model', store=True)
    models = fields.Char(string='Model Name', related='model_id.model', store=True)

    _sql_constraints = [
        ('name_template_uniq', 'unique(name)', "Cannot create duplicate Template Name"),
        ('code_template_uniq', 'unique(code)', "Cannot create duplicate Template Code")
    ]

    @api.constrains('email_to', 'email_cc')
    def _check_email_format(self):
        email_pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")
        for record in self:
            for email in (record.email_to or '').split(','):
                email_clean = email.strip()
                if email_clean and not email_pattern.match(email_clean):
                    raise ValidationError(_("Invalid email address in 'To': %s") % email_clean)

            if record.email_cc:
                for email in record.email_cc.split(','):
                    email_clean = email.strip()
                    if email_clean and not email_pattern.match(email_clean):
                        raise ValidationError(_("Invalid email address in 'CC': %s") % email_clean)

    def _text_to_html(self, text):
        if not text:
            return ''
        sanitized = html_sanitize(text)
        return sanitized.replace('\n', '<br/>')

    def _prepare_html_fields(self, vals):
        if 'header_template' in vals:
            vals['header_templates_html'] = self._text_to_html('<br/>' + vals.get('header_template', ''))
        elif 'header_templates_html' in vals:
            vals['header_templates_html'] = html_sanitize(vals['header_templates_html'])

        if 'bottom_template' in vals:
            vals['bottom_templates_html'] = self._text_to_html('<p/><br/>' + vals.get('bottom_template', ''))
        elif 'bottom_templates_html' in vals:
            vals['bottom_templates_html'] = html_sanitize(vals['bottom_templates_html'])

    @api.model
    def create(self, vals):
        self._prepare_html_fields(vals)
        return super(SANBEMailTemplate, self).create(vals)

    def write(self, vals):
        self._prepare_html_fields(vals)
        return super(SANBEMailTemplate, self).write(vals)
