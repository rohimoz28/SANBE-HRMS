# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
from pytz import UTC

_logger = logging.getLogger(__name__)

class SANBECron(models.Model):
    _name = 'sanbe.mail.scheduler'
    _description = 'Cron for SANBE'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Name',
        store=True
    )
    
    task_mail_ids = fields.One2many('mail.scheduler.task','scheduler_id','Task List')
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company  # Return object, not ID
    )
    branch_id = fields.Many2one(
        'res.branch',
        string='Business Unit',
        required=True
    )
    template_id = fields.Many2one(
        'sanbe.mail.template', 
        string="Template",
        tracking=True
    )
    
    task_code = fields.Char(
        string='Code')
    
    subject = fields.Char(
        string='Subject', 
        related='template_id.subject')
    
    email_to = fields.Text(
        string='To (Email)', 
        related='template_id.email_to',
        tracking=True)

    email_cc = fields.Text(
        string='CC',
        related='template_id.email_cc',
        tracking=True)
    
    header_template = fields.Text(
        string='Header Template',
        related='template_id.header_template',
        help="Content shown at the top of the email.",
    )
    
    bottom_template = fields.Text(
        string='Bottom Template',
        related='template_id.bottom_template',
        help="Content shown at the bottom of the email.",
    )
    
    active = fields.Boolean(
        default=True)
    
    cron_id = fields.Many2one(
        'ir.cron', 
        string='Cron Job', 
    )
    
    models_id = fields.Many2one(
        'ir.model',
        string='Model',
        related='cron_id.model_id',
        store=True,
        tracking=True
    )

    models = fields.Char(
        string='Model Name',
        related='models_id.model',
        store=True,
        tracking=True
    )
    mail_id = fields.Many2one(
        'mail.mail',
        string='Last Mail',
        compute='_compute_last_mail',
        store=True
    )
    @api.depends('mail_ids')
    def _compute_last_mail(self):
        for rec in self:
            if rec.mail_ids:
                # Sort by create_date descending and pick the first
                last_mail = rec.mail_ids.sorted(key=lambda m: m.create_date, reverse=True)[0]
                rec.mail_id = last_mail
            else:
                rec.mail_id = False
    
    message_ids = fields.One2many(
        'mail.message',
        'sanbe_cron_id',
        string='Log Mail',
        domain=[('message_type','=','email_outgoing'),('model','=',models),('subject','=',subject)]
        )
    
    last_state_mail = fields.Selection([
        ('outgoing', 'Outgoing'),
        ('sent', 'Sent'),
        ('received', 'Received'),
        ('exception', 'Delivery Failed'),
        ('cancel', 'Cancelled'),
    ], 
            string='Last Mail Status', 
            readonly=True, 
            copy=False, 
            related='mail_id.state',
            store=True)
    
    failure_type = fields.Selection(selection=[
        # generic
        ("unknown", "Unknown error"),
        # mail
        ("mail_email_invalid", "Invalid email address"),
        ("mail_email_missing", "Missing email"),
        ("mail_from_invalid", "Invalid from address"),
        ("mail_from_missing", "Missing from address"),
        ("mail_smtp", "Connection failed (outgoing mail server problem)"),
        # mass mode
        ("mail_bl", "Blacklisted Address"),
        ("mail_optout", "Opted Out"),
        ("mail_dup", "Duplicated Email"),
        ], string='Failure type', tracking=True)
    
    failure_reason = fields.Text(
        'Failure Reason', readonly=True, copy=False,
        help="Failure reason. This is usually the exception thrown by the email server, stored to ease the debugging of mailing issues.", 
        tracking=True)

    cron_interval = fields.Integer( 
        string='Cron Interval Number', 
        store=True,
        tracking=True,
        default=1
    )
    
    cron_duration = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months')],
        string='Cron Interval', 
        store=True,
        tracking=True,
        default='months'
    )   
    cron_active = fields.Boolean(
        string='Cron Active',
        store=True, 
        tracking=True,
        readonly=True,
        default=True
    )
    last_cron_exec = fields.Datetime(
        'Last Executed', 
        store=True,
        tracking=True
    )
    
    next_cron_exec = fields.Datetime(
        string='Next Execution',
        compute='_compute_next_cron_exec',
        store=True, 
        tracking=True
    )

    @api.onchange('cron_interval', 'cron_duration', 'last_cron_exec')
    def compute_next_cron_exec(self):
        for line in self:
            line._compute_next_cron_exec()


    @api.depends('cron_interval', 'cron_duration', 'last_cron_exec')
    def _compute_next_cron_exec(self):
        for rec in self:
            rec.next_cron_exec = False  # Default fallback
            base_time = fields.Datetime.now()
            if rec.cron_interval and rec.cron_duration:
                interval = int(rec.cron_interval)
                if rec.last_cron_exec:
                    base_time = rec.last_cron_exec or fields.Datetime.now()
                    next_time = base_time
                    if rec.cron_duration == 'minutes':
                        next_time += timedelta(minutes=interval)
                    elif rec.cron_duration == 'hours':
                        next_time += timedelta(hours=interval)
                    elif rec.cron_duration == 'days':
                        next_time += timedelta(days=interval)
                    elif rec.cron_duration == 'weeks':
                        next_time += timedelta(weeks=interval)
                    elif rec.cron_duration == 'months':
                        next_time += relativedelta(months=interval)
                    rec.next_cron_exec = next_time
                else:
                    base_time =  fields.Datetime.now()
                    next_time = base_time
                    if rec.cron_duration == 'minutes':
                        next_time += timedelta(minutes=interval)
                    elif rec.cron_duration == 'hours':
                        next_time += timedelta(hours=interval)
                    elif rec.cron_duration == 'days':
                        next_time += timedelta(days=interval)
                    elif rec.cron_duration == 'weeks':
                        next_time += timedelta(weeks=interval)
                    elif rec.cron_duration == 'months':
                        next_time += relativedelta(months=interval)
                    rec.next_cron_exec = next_time
                    
    attempt_count = fields.Integer(string="Attempt Count", default=0)
    max_attempts = fields.Integer(string="Max Attempts", default=1)
    
    state_cron = fields.Selection([
        ('draft','Draft'),
        ('run','Active'),
        ('hold','Hold')],
        string='State',
        store=True, 
        tracking=True, 
        default='draft'
    )
    
    count_failed = fields.Integer(
        string='Cron Failed',
        related = 'cron_id.failed_count',
        store=True, 
        tracking=True, 
    )
    
    mail_failed = fields.Integer(
        string='Count Failed',
        compute="_compute_mail_failed",
        store=True,
    )

    mail_ids = fields.One2many(
        'mail.mail',
        'sanbe_cron_id',
        string='Log Mail',
    )
    cron_log_ids = fields.One2many(
        related='cron_id.cron_log',
        string='Log Cron',
    )
    
    
    task_hour = fields.Selection([(str(i), str(i).zfill(2)) for i in range(0, 24)], string="Hour", default="8")
    task_minute = fields.Selection( [('00', '00'), ('15', '15'), ('30', '30'), ('45', '45')], string="Minute", default="00")
                
    def _task_domain_search(self):
        current_datetime = fields.Datetime.now() + timedelta(hours=7)  # Adjust timezone
        current_date = current_datetime.date()  # Get the adjusted date
        current_hour = '{:02d}'.format(current_datetime.hour)  # Format hour to two digits
        domain = [
            ('next_cron_date', '=', current_date),
            ('state_cron', '=', 'run'),
            ('task_hour', '=', current_hour),
        ]
        return domain
    
    
    @api.model
    def _sch_domain_search(self):
        self.env.cr.execute("""
            SELECT id FROM sanbe_mail_scheduler
            WHERE next_cron_exec::date = CURRENT_DATE
        """)
        result = self.env.cr.fetchall()
        ids = [row[0] for row in result]
        domain = [
            ('id', 'in', ids),
            ('state_cron', '=', 'run'),
        ]
        return domain
                
    def running_task_list(self):
        domain = self._sch_domain_search()
        sch = self.env['sanbe.mail.scheduler'].search(domain)
        for line_sch in sch:
            # print(line_sch.id)
            for line_task in self.env['mail.scheduler.task'].search([('scheduler_id','=',line_sch.id),('active', '=', True),('state_cron', '=', 'run')]):
                line_task.process_task()
                line_task.last_cron_exec = fields.Datetime.now()
            line_sch.last_cron_exec = fields.Datetime.now()
            line_sch._compute_next_cron_exec()
        

    @api.depends('subject', 'last_cron_exec', 'state_cron')
    def _compute_mail_failed(self):
        for record in self:
            if record.subject and record.last_cron_exec and record.state_cron == 'run':
                # Convert to UTC and make it naive
                last_exec = record.last_cron_exec - timedelta(hours=7)
                if last_exec.tzinfo:
                    last_exec = last_exec.astimezone(UTC).replace(tzinfo=None)

                domain = [
                    ('subject', '=', record.subject),
                    ('create_date', '>=', last_exec)
                ]
                mails = self.env['mail.mail'].search(domain)
                record.mail_ids = mails
                record.mail_failed = sum(1 for mail in mails if mail.state == 'exception')
            else:
                record.mail_ids = False
                record.mail_failed = 0

    def action_set_draft(self):
        self.write({'state_cron': 'draft'})

    def action_set_run(self):
        for rec in self:
            for task_list in self.env['mail.scheduler.task'].search([('scheduler_id','=',self.id),('state_cron','=','run')]):
                task_list.state_cron = 'run'
            rec.running_task_list()
            rec.write({'state_cron': 'run'})
            
    @api.depends('mail_ids')
    def _compute_count_failed(self):
        for record in self:
            record.count_failed = sum(1 for mail in record.mail_ids if mail.failure_type != False)

    def action_set_hold(self):
        for rec in self:
            rec.write({'state_cron': 'hold'})
        
    def _update_failure_info_from_mails(self):
        """Check related mails and update failure info from the latest failed one."""
        for rec in self:
            # Find the latest failed mail related to this cron
            failed_mail = self.env['mail.mail'].search([
                ('sanbe_cron_id', '=', rec.id),
                ('state', '=', 'exception')
            ], order='create_date desc', limit=1)

            if failed_mail:
                rec.last_state_mail = failed_mail.state
                rec.failure_reason = failed_mail.failure_reason or 'Unknown failure'
                rec.failure_type = self._get_failure_type_from_reason(failed_mail.failure_reason)

    def _get_failure_type_from_reason(self, reason):
        reason = (reason or '').lower()
        if 'invalid' in reason and 'email' in reason:
            return 'mail_email_invalid'
        elif 'missing' in reason and 'email' in reason:
            return 'mail_email_missing'
        elif 'invalid' in reason and 'from' in reason:
            return 'mail_from_invalid'
        elif 'missing' in reason and 'from' in reason:
            return 'mail_from_missing'
        elif 'smtp' in reason or 'server' in reason:
            return 'mail_smtp'
        elif 'blacklist' in reason:
            return 'mail_bl'
        elif 'opt out' in reason or 'opted out' in reason:
            return 'mail_optout'
        elif 'duplicate' in reason:
            return 'mail_dup'
        else:
            return 'unknown'
    
