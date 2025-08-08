# -*- coding: utf-8 -*-
import logging
import threading
import time
from datetime import datetime, timedelta
import pytz
import psycopg2

import odoo
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

_intervalTypes = {
    'minutes': lambda x: timedelta(minutes=x),
    'hours': lambda x: timedelta(hours=x),
    'days': lambda x: timedelta(days=x),
    'weeks': lambda x: timedelta(weeks=x),
}

def _log_cron_failure(env, cron_id=None, name='', level='exception', error='', problem_type='unknown'):
    env['cron.failure.log'].create({
        'cron_id': cron_id,
        'name': name or str(cron_id),
        'level': level,
        'error_log': str(error),
        'problem_type': problem_type,
    })

def _detect_problem_type(e):
    msg = str(e).lower()
    if isinstance(e, ValidationError):
        return 'data_error'
    elif isinstance(e, UserError):
        return 'permission_error'
    elif 'timeout' in msg:
        return 'timeout'
    elif 'record does not exist' in msg or 'not found' in msg:
        return 'record_missing'
    elif isinstance(e, psycopg2.ProgrammingError) and e.pgcode == '42P01':
        return 'model_missing'
    else:
        return 'runtime_error'

class CronFailureHistory(models.Model):
    _name = 'cron.failure.log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Cron Failure History'

    cron_id = fields.Many2one('ir.cron', string='Cron Job')
    name = fields.Char(string='Name', help="Failed cron action name")
    level = fields.Selection([
        ('info', 'Info'),
        ('debug', 'Debug'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('exception', 'Exception')
    ], string='Level', help="Log level")
    error_log = fields.Char(string='Error Details', help="Detailed description about error")
    model_name = fields.Char(string='Model')
    method_name = fields.Char(string='Method')
    traceback = fields.Text(string='Traceback')
    failed_at = fields.Datetime(string='Failed At', default=fields.Datetime.now)
    problem_type = fields.Selection([
        ('model_missing', 'Model Missing'),
        ('method_missing', 'Method Missing'),
        ('record_missing', 'Record Not Found'),
        ('permission_error', 'Permission Error'),
        ('data_error', 'Data Error'),
        ('runtime_error', 'Runtime Error'),
        ('external_service', 'External Service Failure'),
        ('timeout', 'Timeout'),
        ('manual_process', 'Manual Process'),
        ('unknown', 'Unknown Error'),
    ], string="Problem Type", default='unknown')

    # ➕ Added missing fields used in _log_task_execution
    task_id = fields.Many2one('mail.scheduler.task', string='Task')
    state = fields.Selection([
        ('info', 'Info'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='Execution State')
    message = fields.Text(string='Message')
    exception_detail = fields.Text(string='Message')
    executed_at = fields.Datetime(string='Executed At')
    user_id = fields.Many2one('res.users', string='Executed By')

class IrCron(models.Model):
    _inherit = 'ir.cron'

    failed_count = fields.Integer(
        string="Failed Count", 
        default=0, 
        store=True)
    
    cron_log = fields.One2many(
        'cron.failure.log',
        'cron_id',
        string="Log Cron Information")
    
    sanbe_cron_id = fields.Many2one(
        'sanbe.mail.scheduler',
        string="Sanbe Cron ID")


    def method_direct_trigger(self):
        self.check_access_rights('write')
        for cron in self:
            cron._try_lock()
            _logger.info('Manually starting job `%s`.', cron.name)
            _log_cron_failure(self.env, cron_id=self.id, level='info',
                                          name=str(self.cron_name),
                                          error='Manually processing the job.',
                                          problem_type='manual_process')
            cron.with_user(cron.user_id).with_context({'lastcall': cron.lastcall}).ir_actions_server_id.run()
            self.env.flush_all()
            _logger.info('Job `%s` done.', cron.name)
            cron.lastcall = fields.Datetime.now()
        return True

    @classmethod
    def _process_jobs(cls, db_name):
        try:
            db = odoo.sql_db.db_connect(db_name)
            threading.current_thread().dbname = db_name
            with db.cursor() as cron_cr:
                cls._check_version(cron_cr)
                jobs = cls._get_all_ready_jobs(cron_cr)
                if not jobs:
                    return
                cls._check_modules_state(cron_cr, jobs)

                for job_id in (job['id'] for job in jobs):
                    env = api.Environment(cron_cr, odoo.SUPERUSER_ID, {})
                    try:
                        job = cls._acquire_one_job(cron_cr, (job_id,))
                    except psycopg2.extensions.TransactionRollbackError:
                        cron_cr.rollback()
                        _logger.debug("Job %s has been processed by another worker, skip", job_id)
                        _log_cron_failure(env, cron_id=job_id, level='debug',
                                          name=str(job_id),
                                          error='Job acquired by another worker.',
                                          problem_type='debug')
                        continue

                    if not job:
                        _logger.debug("Another worker is processing job %s, skip", job_id)
                        _log_cron_failure(env, cron_id=job_id, level='debug',
                                          name=str(job_id),
                                          error='Another worker is processing the job.',
                                          problem_type='debug')
                        continue

                    try:
                        registry = odoo.registry(db_name)
                        registry[cls._name]._process_job(db, cron_cr, job)
                        cron_cr.commit()
                    except Exception as e:
                        _logger.exception("Error executing job %s", job_id)
                        problem_type = _detect_problem_type(e)
                        _log_cron_failure(env, cron_id=job_id, name=job['cron_name'],
                                          level='exception', error=str(e),
                                          problem_type=problem_type)
                        cron_cr.rollback()
        except psycopg2.ProgrammingError as e:
            if e.pgcode == '42P01':
                _logger.warning('Undefined table in DB %s.', db_name)
            else:
                raise
        except Exception as e:
            if 'base version mismatch' in str(e).lower():
                _logger.warning('Skipping DB %s due to base version mismatch.', db_name)
            elif 'module state issue' in str(e).lower():
                _logger.warning('Skipping DB %s due to module state issue.', db_name)
            else:
                _logger.warning('Exception in cron job loop for DB %s', db_name, exc_info=True)
        finally:
            if hasattr(threading.current_thread(), 'dbname'):
                del threading.current_thread().dbname

    @classmethod
    def _process_job(cls, db, cron_cr, job):
        if job['interval_number'] <= 0:
            _logger.error("Job %s (%s) disabled due to invalid interval.", job['id'], job['cron_name'])
            cron_cr.execute("UPDATE ir_cron SET active=false WHERE id=%s", [job['id']])
            env = api.Environment(cron_cr, odoo.SUPERUSER_ID, {})
            _log_cron_failure(env, cron_id=job['id'], name=job['cron_name'], level='error',
                              error='Interval number is null or negative; job disabled.',
                              problem_type='data_error')
            return

        lastcall = fields.Datetime.to_datetime(job['lastcall']) if job['lastcall'] else None
        interval = _intervalTypes.get(job['interval_type'], lambda x: timedelta(minutes=x))(job['interval_number'])
        env = api.Environment(cron_cr, job['user_id'], {'lastcall': lastcall})
        ir_cron = env[cls._name]

        now = fields.Datetime.context_timestamp(ir_cron, datetime.utcnow())
        past_nextcall = fields.Datetime.context_timestamp(ir_cron, fields.Datetime.to_datetime(job['nextcall'])) if job['nextcall'] else now

        missed_call = past_nextcall
        missed_call_count = 0
        while missed_call <= now:
            missed_call += interval
            missed_call_count += 1
        future_nextcall = missed_call

        effective_call_count = (
            1 if missed_call_count == 0
            else 1 if not job['doall']
            else missed_call_count if job['numbercall'] == -1
            else min(missed_call_count, job['numbercall'])
        )
        call_count_left = max(job['numbercall'] - effective_call_count, -1)

        for _ in range(effective_call_count):
            ir_cron._callback(job['cron_name'], job['ir_actions_server_id'], job['id'])

        cron_cr.execute("""
            UPDATE ir_cron
            SET nextcall=%s,
                numbercall=%s,
                lastcall=%s,
                active=%s
            WHERE id=%s
        """, [
            fields.Datetime.to_string(future_nextcall.astimezone(pytz.UTC)),
            call_count_left,
            fields.Datetime.to_string(now.astimezone(pytz.UTC)),
            job['active'] and bool(call_count_left),
            job['id'],
        ])

        cron_cr.execute("""
            DELETE FROM ir_cron_trigger
            WHERE cron_id = %s AND call_at < (now() at time zone 'UTC')
        """, [job['id']])

    @api.model
    def _callback(self, cron_name, server_action_id, job_id):
        try:
            # Remove or comment out the following line; env.clear() does not exist
            # self.env.clear()

            _logger.info('Starting job `%s`.', cron_name)
            start_time = time.time() if _logger.isEnabledFor(logging.DEBUG) else None

            self.env['ir.actions.server'].browse(server_action_id).run()

            _logger.info('Job `%s` done.', cron_name)

            cron = self.env['ir.cron'].browse(job_id)
            cron.failed_count = 0

            if start_time:
                end_time = time.time()
                _logger.debug('%.3fs (cron %s, server action %d with uid %d)',
                              end_time - start_time, cron_name,
                              server_action_id, self.env.uid)

        except Exception as e:
            # Use self.pool.reset_changes() if needed
            if hasattr(self, 'pool') and self.pool:
                self.pool.reset_changes()

            _logger.exception("Call from cron %s for server action #%s failed (Job %s)", cron_name, server_action_id, job_id)

            problem_type = _detect_problem_type(e)

            _log_cron_failure(self.env, cron_id=job_id, name=cron_name,
                              level='exception', error=str(e),
                              problem_type=problem_type)

            cron = self.env['ir.cron'].browse(job_id)
            cron.failed_count += 1
