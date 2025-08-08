# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime,timedelta
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
        compute='_compute_cron_info',
        inverse='_inverse_cron_info',
        store=True,
        tracking=True
    )
    
    cron_duration = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months')],
        string='Cron Interval', 
        compute='_compute_cron_info', 
        inverse='_inverse_cron_info', 
        store=True,
        tracking=True
    )
    cron_active = fields.Boolean(
        string='Cron Active',
        related='cron_id.active',
        store=True, 
        tracking=True,
        readonly=True
    )
    last_cron_exec = fields.Datetime(
        'Last Executed', 
        related='cron_id.lastcall', 
        store=True,
        tracking=True
    )
    
    attempt_count = fields.Integer(string="Attempt Count", default=0)
    max_attempts = fields.Integer(string="Max Attempts", default=4)
    
    next_cron_exec = fields.Datetime(
        string='Next Execution',
        compute='_get_cron',
        store=True, 
        tracking=True
    )
    
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
    
    
    def _get_cron(self):
        for line in self:
            cr = self.env.cr
            query = """ SELECT 
                            ic.id cron_id,
                            im.id model_id,
                            ic.nextcall::date AS nextcall,
                            ic.lastcall::date AS lastcall,
                            EXTRACT(HOUR FROM ic.lastcall)::char AS lastcall_hour
                        FROM 
                            ir_cron ic
                        LEFT JOIN 
                            ir_act_server ias ON ic.ir_actions_server_id = ias.id
                        LEFT JOIN 
                            ir_model im ON ias.model_id = im.id
                        WHERE 
                            im.model ILIKE 'mail.message.schedule';
            """
            cr.execute(query)
            for cron_id, model_id,nextcall,lastcall,lastcall_hour in cr.fetchall():
                line.cron_id = self.env['ir.cron'].sudo().browse(cron_id)
                line.cron_id = self.env['ir.model'].sudo().browse(model_id)
                line.next_cron_exec = nextcall
                line.last_cron_exec = lastcall
                line.last_cron_hour = lastcall_hour
                
    def _task_domain_search(self):
        current_date = fields.Date.today()  # or however you define it
        current_hours = fields.Datetime.now().hour  # for example

        domain = [
            ('next_cron_date', '=', current_date),
            ('active', '=', True),
            ('task_hour', '>=', current_hours),
        ]
        return domain
                
                
    def running_task_list(self):
        domain = self._contract_domain_search()
        task = self.env['mail.scheduler.task'].search(domain)
        for task_list in task:
            task_list.process_task()
            task_list.last_cron_exec = fields.Datetime.now()
        

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

    @api.depends('cron_id')
    def _compute_cron_info(self):
        for rec in self:
            cron = rec.cron_id
            rec.next_cron_exec = cron.nextcall if cron else False
            rec.cron_interval = cron.interval_number if cron else 1
            rec.cron_duration = cron.interval_type if cron else 'months'

    def _inverse_cron_info(self):
        for rec in self:
            cron = rec.cron_id
            if cron:
                if rec.next_cron_exec:
                    cron.nextcall = rec.next_cron_exec
                if rec.cron_duration:
                    cron.interval_type = rec.cron_duration
                if rec.cron_interval:
                    if rec.cron_interval < 1:
                        raise UserError(_('Interval number must be greater than 0'))
                    cron.interval_number = rec.cron_interval
                cron.active = rec.cron_active

    def action_set_draft(self):
        self.write({'state_cron': 'draft'})

    def action_set_run(self):
        for rec in self:
            if rec.cron_id and hasattr(rec.cron_id, 'method_direct_trigger'):
                rec.cron_id.lastcall = datetime.now()
                rec.cron_id.method_direct_trigger()
                rec.cron_id.failed_count = 0
                rec.cron_id.active = True
            rec.write({'state_cron': 'run'})
            
    @api.depends('mail_ids')
    def _compute_count_failed(self):
        for record in self:
            # raise UserError('Kesini')
            record.count_failed = sum(1 for mail in record.mail_ids if mail.failure_type != False)

    def action_set_hold(self):
        if self.cron_id:
            self.cron_id.active = False
            self.cron_id.lastcall = False
            self.write({'state_cron': 'hold'})
        
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
    
