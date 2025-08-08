# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    sanbe_tempate_id = fields.Many2one(
        'sanbe.mail.template',
        string="Sanbe Mail Template")
    
    failed_delivery_count = fields.Integer(
        string="Failed Delivery Count", 
        default=0)

class MailMail(models.Model):
    _inherit = 'mail.mail'

    sanbe_tempate_id = fields.Many2one(
        'sanbe.mail.template',
        string="Sanbe Mail Template")
    
    sanbe_cron_id = fields.Many2one(
        'sanbe.mail.scheduler',
        string="Sanbe Cron ID")
    

class Message(models.Model):
    _inherit = 'mail.message'
    
    sanbe_cron_id = fields.Many2one(
        'sanbe.mail.scheduler',
        string="Sanbe Cron ID")
    
    email_to = fields.Text(
        string='To (Email)',
        related='sanbe_cron_id.email_to',
        store=True
    )