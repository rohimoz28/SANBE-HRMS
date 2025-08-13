# -*- coding: utf-8 -*-
import logging
import re
import ast
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta
from pytz import UTC
from odoo.tools import html_escape, html_sanitize, html2plaintext

_logger = logging.getLogger(__name__)


class SANBECronTask(models.Model):  
    _name = 'mail.scheduler.task'  # Or use 'sanbe_mail.scheduler.task' if you change your access file
    _description = 'Task List SANBE'
    _rec_name = 'name'
    _order = 'next_cron_exec asc,scheduler_id asc' 
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Main Fields
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    active = fields.Boolean(default=True)
    task_code = fields.Char(string='Code')
    scheduler_id = fields.Many2one('sanbe.mail.scheduler', string='Scheduler')
    branch_id = fields.Many2one('res.branch', string='Branch', related='scheduler_id.branch_id', store=True)
    attempt_count = fields.Integer(string="Attempt Count",store=True,default=0)
    max_attempts = fields.Integer(string="Max Attempts",store=True, related='scheduler_id.max_attempts')

    # Company / Branch
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    branch_id = fields.Many2one('res.branch', string='Business Unit', related='scheduler_id.branch_id')

    # Mail Template
    template_id = fields.Many2one('sanbe.mail.template', string="Template", tracking=True)
    subject = fields.Char(string='Subject', related='template_id.subject')
    email_to = fields.Text(string='To (Email)', related='template_id.email_to', tracking=True,store=True)
    email_cc = fields.Text(string='CC', related='template_id.email_cc', tracking=True)
    header_template = fields.Text(string='Header Template', related='template_id.header_template', help="Top of email",store=True)
    bottom_template = fields.Text(string='Bottom Template', related='template_id.bottom_template', help="Bottom of email",store=True)

    header_templates_html = fields.Html(string='Header Template', related='template_id.header_templates_html', help="Top of email",store=True)
    bottom_templates_html = fields.Html(string='Bottom Template', related='template_id.bottom_templates_html', help="Bottom of email",store=True)
    # Cron Config
    cron_id = fields.Many2one('ir.cron', string='Cron Job')
    cron_interval = fields.Integer(string='Cron Interval Number', store=True, tracking=True)
    cron_duration = fields.Selection([
        ('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days'),
        ('weeks', 'Weeks'), ('months', 'Months')
    ], string='Cron Interval', store=True, tracking=True)
    cron_active = fields.Boolean(string='Cron Active', related='cron_id.active', store=True, tracking=True, readonly=True)
    count_failed = fields.Integer(string='Cron Failed', related='cron_id.failed_count', store=True, tracking=True)
    date = fields.Integer(string='Cron Failed', related='cron_id.failed_count', store=True, tracking=True)
    last_cron_exec = fields.Datetime('Last Executed', store=True, tracking=True, readonly=True)
    next_cron_exec = fields.Datetime(string='Next Execution', store=True, tracking=True)

    last_cron_date = fields.Date(string="Last Executed Date", compute="_compute_date_only")
    next_cron_date = fields.Date(string="Next Execution Date", compute="_compute_date_only", inverse='_compute_combined_datetime')

    task_hour = fields.Selection([(str(i), str(i).zfill(2)) for i in range(0, 24)], string="Hour", default="8")
    task_minute = fields.Selection([('00', '00'), ('15', '15'), ('30', '30'), ('45', '45')], string="Minute", default="00")
    task_time = fields.Char(string="Start Time", compute="_compute_start_time", store=True)

    # ✅ Computed datetime from date + hour + minute
    computed_next_cron_exec = fields.Datetime(
        string="Next Execution (From Date + Time)",
        compute="_compute_combined_datetime",
        inverse="_inverse_combined_datetime",
        store=True
    )


    @api.depends('task_hour', 'task_minute')
    def _compute_start_time(self):
        for rec in self:
            if rec.task_hour and rec.task_minute:
                rec.task_time = f"{rec.task_hour.zfill(2)}:{rec.task_minute.zfill(2)}"
            else:
                rec.task_time = False

    @api.depends('last_cron_exec', 'next_cron_exec')
    def _compute_date_only(self):
        for rec in self:
            rec.last_cron_date = rec.last_cron_exec.date() if rec.last_cron_exec else False
            rec.next_cron_date = rec.next_cron_exec.date() if rec.next_cron_exec else False

    @api.depends('next_cron_date', 'task_hour', 'task_minute')
    def _compute_combined_datetime(self):
        for rec in self:
            if rec.next_cron_date and rec.task_hour and rec.task_minute:
                start_datetime = f"{rec.next_cron_date} {rec.task_hour}:{rec.task_minute}:00"
                date_starts = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
                rec.next_cron_exec = date_starts
            else:
                rec.next_cron_exec = False

    def _inverse_combined_datetime(self):
        for rec in self:
            dt = rec.computed_next_cron_exec
            if dt:
                rec.next_cron_exec = dt
                rec.task_hour = str(dt.hour)
                rec.task_minute = str(dt.minute).zfill(2)
                rec.next_cron_date = dt.date()
            else:
                rec.next_cron_exec = False    

    # Mail Tracking
    mail_ids = fields.One2many('mail.mail', 'sanbe_cron_id', string='Log Mail')
    mail_id = fields.Many2one('mail.mail', string='Last Mail', compute='_compute_last_mail', store=True)
    mail_failed = fields.Integer(string='Count Failed', compute="_compute_mail_failed", store=True)
    last_state_mail = fields.Selection([
        ('outgoing', 'Outgoing'), ('sent', 'Sent'), ('received', 'Received'),
        ('exception', 'Delivery Failed'), ('cancel', 'Cancelled')
    ], string='Last Mail Status', readonly=True, copy=False, related='mail_id.state', store=True)
    failure_type = fields.Selection([
        ("unknown", "Unknown error"), ("mail_email_invalid", "Invalid email address"),
        ("mail_email_missing", "Missing email"), ("mail_from_invalid", "Invalid from address"),
        ("mail_from_missing", "Missing from address"), ("mail_smtp", "Connection failed"),
        ("mail_bl", "Blacklisted Address"), ("mail_optout", "Opted Out"),
        ("mail_dup", "Duplicated Email")
    ], string='Failure type', tracking=True)
    failure_reason = fields.Text('Failure Reason', related="mail_id.failure_reason", readonly=True, store=True, copy=False, help="Email server error", tracking=True)    
    # Model Related
    model_id = fields.Many2one('ir.model', string='Model', store=True, tracking=True)
    models = fields.Char(string='Model Name', related='model_id.model', store=True, tracking=True)
    
    
    @api.depends('template_id','model_id')
    def _set_model_template(self):
        for line in self:
            if line.template_id and line.model_id:
                line.template_id.model_id = line.model_id


    # Logs
    cron_log_ids = fields.One2many(related='cron_id.cron_log', string='Log Cron')
    message_ids = fields.One2many(
        'mail.message',
        'sanbe_cron_id',
        string='Log Mail',
        domain=[('message_type', '=', 'email_outgoing')]
    )

    # State
    state_cron = fields.Selection([
        ('draft', 'Draft'), ('run', 'Active'), ('hold', 'Hold')
    ], string='State', store=True, tracking=True, default='draft')

    def re_active_task(self):
        for line in self:        
            context = context or {}
            if line.state_cron != 'run':
                line.state_cron = 'run'
                line.process_task(context=context)

    ########    execution like ir.con but it dooesn't add argument  
    # model ke 1  
    # def process_task(self):
    #     for task in self:
    #         while task.attempt_count < task.max_attempts:
    #             try:
    #                 model = task.env[task.models]
    #                 if not hasattr(model, task.task_code):
    #                     task.failure_reason = ( f"Function {task.task_code} not found on model {task.models}" )
    #                     raise UserError(task.failure_reason)
    #                 method = getattr(model, task.task_code)
    #                 method()
    #                 task.failure_reason = False
    #                 task.attempt_count = 0
    #                 break

    #             except Exception as e:
    #                 task.attempt_count += 1
    #                 task.failure_reason = str(e)
    #                 if task.attempt_count >= task.max_attempts:
    #                     break
    
    
    # def parse_args_kwargs_with_context(self, raw_args, context):
    #     source = f"f({raw_args})"
    #     module = ast.parse(source, mode='exec')
    #     call = module.body[0].value

    #     args = []
    #     for arg in call.args:
    #         if isinstance(arg, ast.Name) and arg.id in context:
    #             args.append(context[arg.id])
    #         else:
    #             args.append(ast.literal_eval(arg))

    #     kwargs = {}
    #     for kw in call.keywords:
    #         if isinstance(kw.value, ast.Name) and kw.value.id in context:
    #             kwargs[kw.arg] = context[kw.value.id]
    #         else:
    #             kwargs[kw.arg] = ast.literal_eval(kw.value)

    #     return args, kwargs

    # # 1. process_task ->> hanya menjalankan 1 task
    # # 2. process_task ini dipanggil di method self.process_all_tasks()
    # # 3. process_all_tasks() dipanggil di mail_scheduler_task.running_task_list()
    # # 4. untuk debuggin buat button pada mail scheduler dg nama Running Task List ->> running_task_list
    # def process_task(self, context=None):
    #     # branch_id = self.branch_id
    #     self.ensure_one()  # pastikan cuma 1 record
    #     context = context or {}
    #     for task in self:
    #         model = task.env[task.models]
    #         match = re.match(r'^(\w+)\((.*)\)$', task.task_code.strip())
    #         if not match:
    #             task.failure_reason = f"Invalid task_code format: {task.task_code}"
    #             task.attempt_count += 1
    #             if task.attempt_count >= task.max_attempts:
    #                 task.state_cron = 'hold'
    #                 break
    #         method_name, raw_args = match.groups()
    #         method_name = method_name.strip()
    #         raw_args = raw_args.strip()
    #         method = getattr(model, method_name)
    #         if not hasattr(model, method_name):
    #             task.failure_reason = (
    #                 f"Function '{method_name}' not found on model '{task.models}'"
    #             )
    #             task.attempt_count += 1
    #             if task.attempt_count >= task.max_attempts:
    #                 task.state_cron = 'hold'
    #                 break
    #         if task.attempt_count < task.max_attempts:
    #             if raw_args:
    #                 args, kwargs = self.parse_args_kwargs_with_context(raw_args, context)
    #             else:
    #                 args, kwargs = [], {}
    #             try:
    #                 print('args',*args)
    #                 print('kwargs',**kwargs)
    #                 branch = self.env['res.branch'].browse(*args)
    #                 dynamic_data = method(*args, **kwargs)
    #                 email_body = f"""
    #                     {html2plaintext(task.header_templates_html.format(
    #                             today=datetime.today().strftime("%d-%b-%Y") ,
    #                             branch=branch.name,
    #                         ))}<br/><br/>
    #                     {dynamic_data}<br/><br/>
    #                     {html2plaintext(task.bottom_templates_html)}
    #                     """
    #                 email_values = {
    #                     'subject': task.subject,
    #                     'email_to': task.email_to,
    #                     'email_cc': task.email_cc,
    #                     'email_from': 'System Administrator <donotreply@sanbe-farma.com>',
    #                     'body_html': email_body,
    #                 }
    #                 task.template_id.mail_template_id.sudo().write(email_values)
    #                 self.env['mail.mail'].sudo().create(email_values).send()
    #                 # task.template_id.mail_template_id.with_context().send_mail(task.id,force_send=True)
                    
    #                 task.failure_reason = ''
    #                 task.attempt_count = 0
    #                 task.last_cron_exec = fields.Datetime.now()
    #                 break
    #             except Exception as e:
    #                 task.attempt_count += 1
    #                 task.failure_reason = str(e)
    #                 task.state_cron = 'hold'

    def eval_node(self, node, context):
        if isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            else:
                raise ValueError(f"Name '{node.id}' not found in context")
        elif isinstance(node, ast.Attribute):
            value = self.eval_node(node.value, context)
            return getattr(value, node.attr)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Str):  # py<3.8 compatibility
            return node.s
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Dict):
            return {self.eval_node(k, context): self.eval_node(v, context) for k, v in zip(node.keys, node.values)}
        elif isinstance(node, ast.List):
            return [self.eval_node(e, context) for e in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(self.eval_node(e, context) for e in node.elts)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self.eval_node(node.operand, context)
        else:
            try:
                return ast.literal_eval(node)
            except Exception:
                self.failure_reason = f"Unsupported expression: {ast.dump(node)}"
                if self.attempt_count >= self.max_attempts:
                    self.state_cron = 'hold'
                raise ValueError(f"Unsupported expression: {ast.dump(node)}")

    def process_task(self, context=None):
        self.ensure_one()
        context = context or {}
        for task in self:
            if task.state_cron == 'run':
                exec_context = {
                    'self': task,
                    'env': task.env,
                    'fields': fields,
                    'datetime': datetime,
                }
                exec_context.update(context)

                if not task.task_code:
                    task.failure_reason = "No task_code defined"
                    task.attempt_count += 1
                    if task.attempt_count >= task.max_attempts:
                        task.state_cron = 'hold'
                    continue

                model = task.env[task.models]
                match = re.match(r'^(\w+)\((.*)\)$', task.task_code.strip())
                if not match:
                    task.failure_reason = f"Invalid task_code format: {task.task_code}"
                    task.attempt_count += 1
                    if task.attempt_count >= task.max_attempts:
                        task.state_cron = 'hold'
                    continue

                method_name, raw_args = match.groups()
                method_name = method_name.strip()
                raw_args = raw_args.strip()

                if not hasattr(model, method_name):
                    task.failure_reason = f"Function '{method_name}' not found on model '{task.models}'"
                    task.attempt_count += 1
                    if task.attempt_count >= task.max_attempts:
                        task.state_cron = 'hold'
                    continue

                if task.attempt_count >= task.max_attempts:
                    continue

                try:
                    if raw_args:
                        args, kwargs = self.parse_args_kwargs_with_context(raw_args, exec_context)
                    else:
                        args, kwargs = [], {}

                    result = getattr(model, method_name)(*args, **kwargs)
                    print(*args)
                    print(*kwargs)
                    # Reset failure and attempt count on success
                    email_body = f"""
                        {html2plaintext(task.header_templates_html.format(
                                today=datetime.today().strftime("%d-%b-%Y") ,
                                branch=self.branch_id.name,
                            ))}<br/><br/>
                        {result}<br/><br/>
                        {html2plaintext(task.bottom_templates_html)}
                        """
                    email_values = {
                        'subject': task.subject,
                        'email_to': task.email_to,
                        'email_cc': task.email_cc,
                        'email_from': 'System Administrator <donotreply@sanbe-farma.com>',
                        'body_html': email_body,
                    }
                    task.template_id.mail_template_id.sudo().write(email_values)
                    self.env['mail.mail'].sudo().create(email_values).send()
                    # task.template_id.mail_template_id.with_context().send_mail(task.id,force_send=True)
                    task.attempt_count = 0
                    task.failure_reason = ''
                    task.last_cron_exec = fields.Datetime.now()
                    task.state_cron = 'run'

                except Exception as e:
                    task.attempt_count += 1
                    task.failure_reason = str(e)
                    _logger.error(f"Error processing task {task.name}: {e}")
                    if task.attempt_count >= task.max_attempts:
                        task.state_cron = 'hold'

    def parse_args_kwargs_with_context(self, raw_args, context):
        source = f"f({raw_args})"
        module = ast.parse(source, mode='exec')
        call = module.body[0].value
        args = [self.eval_node(arg, context) for arg in call.args]
        kwargs = {kw.arg: self.eval_node(kw.value, context) for kw in call.keywords}
        return args, kwargs

    def process_all_pending_tasks(self, context=None):
        """
        Cari task yang gagal tapi belum melewati max_attempts,
        lalu proses semua task itu dengan context opsional.
        """
        context = context or {}
        tasks = self.search([
            ('attempt_count', '<', 4),
            ('failure_reason', '!=', False),
        ])
        if tasks:
            tasks.process_task(context=context)

    # looping semua scheduler_id.task_mail_ids
    # didalam func itu menjalankan process_task()
    def process_all_tasks(self):
        current_hour = str(datetime.now().hour)
        context = context or {}
        for task in self.env['mail.scheduler.task'].search([('next_cron_date','=',datetime.today()),('task_hour','=',current_hour)]):            
            if task:
                task.process_task(context=context)

    # Compute Fields
    @api.depends('template_id', 'branch_id')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.template_id.name or 'Template'} - {rec.branch_id.name or 'Branch'}"

    @api.depends('mail_ids')
    def _compute_last_mail(self):
        for rec in self:
            rec.mail_id = rec.mail_ids.sorted(key=lambda m: m.create_date, reverse=True)[0] if rec.mail_ids else False

    @api.depends('mail_ids')
    def _compute_mail_failed(self):
        for rec in self:
            rec.mail_failed = sum(1 for mail in rec.mail_ids if mail.state == 'exception')

    # Actions
    def action_set_draft(self):
        self.write({'state_cron': 'draft'})

    # Utility
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
        
    @api.model
    def create(self, vals):
        record = super(SANBECronTask, self).create(vals)
        if record.template_id and record.model_id:
            record.template_id.model_id = record.model_id
            record.template_id.mail_template_id.model_id = record.model_id
        return record


    def write(self, vals):
        res = super(SANBECronTask, self).write(vals)
        
        for rec in self:
            # Sinkronisasi model_id ke template jika model_id berubah
            if 'model_id' in vals:
                if rec.template_id:
                    rec.template_id.model_id = rec.model_id
                    if rec.template_id.mail_template_id:
                        rec.template_id.mail_template_id.model_id = rec.model_id
            
            # Set failure_type jika failure_reason diubah
            if 'failure_reason' in vals:
                failure_type = rec._get_failure_type_from_reason(vals['failure_reason'])
                rec.failure_type = failure_type

        return res

    def act_resend_msg(self):
        for line in self:
            line.mail_id.send()
        self.write({'state_cron': 'draft'})