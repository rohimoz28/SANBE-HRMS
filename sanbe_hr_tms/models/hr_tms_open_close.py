# -*- coding : utf-8 -*-
#################################################################################
# Author    => Albertus Restiyanto Pramayudha
# email     => xabre0010@gmail.com
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA
#################################################################################
# from Demos.FileSecurityTest import permissions
import pdb

from odoo import fields, models, api, _, Command
from odoo.exceptions import ValidationError,UserError
from odoo.osv import expression
import pytz
from datetime import timedelta, datetime, time,date
import dateutil.parser
import holidays
from datetime import datetime
date_format = "%Y-%m-%d"
from odoo.exceptions import AccessError, MissingError, UserError
import requests
import logging
from psycopg2 import OperationalError, errorcodes

_logger = logging.getLogger(__name__)

chari = {'0':6,'1':0,'2':1,'3':2,'4':3,'5':4,'6':5}

class HRTmsOpenClose(models.Model):
    _name = "hr.opening.closing"
    _description = 'HR TMS Open And Close'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id DESC'

    @api.depends('area_id')
    def _isi_semua_branch(self):
        for allrecs in self:
            databranch = []
            for allrec in allrecs.area_id.branch_id:
                mybranch = self.env['res.branch'].search([('name','=', allrec.name)], limit=1)
                databranch.append(mybranch.id)
            allbranch = self.env['res.branch'].sudo().search([('id','in', databranch)])
            allrecs.branch_ids=[Command.set(allbranch.ids)]

    # @api.depends('branch_id')
    # def _isi_semua_branch(self):
    #     for record in self:
    #         resbranch = self.env['res.branch'].sudo().search([])
    #         branch = resbranch.filtered(lambda p: p.id == record.branch_id)
    #         record.branch_ids = branch.id

    name = fields.Char('Period Name')
    area_id = fields.Many2one('res.territory',string='Area', index=True )
    branch_ids = fields.Many2many('res.branch', 'res_branch_rel', string='AllBranch', compute='_isi_semua_branch',
                                  store=False)
    branch_id = fields.Many2one('res.branch',string='Business Unit',index=True,domain="[('id','in',branch_ids)]")
    open_periode_from = fields.Date('Opening Periode From')
    open_periode_to = fields.Date('Opening Periode To')
    close_periode_from = fields.Date('Closing Periode From')
    close_periode_to = fields.Date('Closing Periode To')
    isopen = fields.Boolean('Is Open',default=False)
    state_process = fields.Selection(
        [
            ('draft', 'Draft'),
            ('running', 'Running'),
            ('done', 'Close'),
            ('transfer_to_payroll', 'Transfer To Payroll')
        ],
        default='draft',
        String='Process State',
        tracking=True)
    show_process_button = fields.Boolean(
        string='Show Process Button',
        compute='_compute_show_process_button',
        store=False,  # Selalu compute fresh
    )
    processing_user_id = fields.Many2one(
        'res.users',
        string='Processing By',
        readonly=True,
        help='User yang sedang memproses record ini'
    )
    processing_start = fields.Datetime(
        string='Processing Started',
        readonly=True
    )

    @api.depends('state_process')
    def _compute_show_process_button(self):
        """
        Button SELALU muncul jika state = running
        Tidak peduli siapa yang sedang proses
        """
        for rec in self:
            rec.show_process_button = (rec.state_process == 'running')

    def kumpulhari(self,wd1,wd2):
        listhr = []
        wda = wd1
        wdb = wd2
        while wda != wdb:
            listhr.append(chari[str(wda)])
            wda += 1
            if wda == 7 : wda = 0
        listhr.append(chari[str(wdb)])
        return listhr
    
    @api.model_create_multi
    def create(self, values):
        for vals in values:
            if ('branch_id' in vals) and ('open_periode_from' in vals):
                if 'open_periode_from' in vals:
                    br = self.env['res.branch'].sudo().search([('id', '=', vals['branch_id'])])
                    date_obj = datetime.strptime(vals['open_periode_to'], "%Y-%m-%d")
                    vals['name'] = date_obj.strftime("%B %Y") + ' | ' + br['name']
                    check = self.env['hr.tmsentry.summary'].sudo().search([
                        ('branch_id', '=', br.id),
                        ('date_from', '<=', datetime.strptime(str(vals['open_periode_from']),"%Y-%m-%d").date()),
                        ('date_to', '>=', datetime.strptime(str(vals['open_periode_from']), "%Y-%m-%d").date())
                    ])
                    if check:
                        raise UserError('Open Periode From for This Branch Already Used')
                    check = self.env['hr.tmsentry.summary'].sudo().search([
                        ('branch_id', '=', br.id),
                        ('date_from', '<=', datetime.strptime(str(vals['open_periode_to']), "%Y-%m-%d").date()),
                        ('date_to', '>=', datetime.strptime(str(vals['open_periode_to']), "%Y-%m-%d").date())])
                    if check:
                        raise UserError('Tanggal period ini sudah di gunakan')
            else:
                raise UserError('Branch or Open Periode From Not Selected')

            existing_record = self.search([('branch_id', '=', vals['branch_id']), ('state_process', '=', 'running')])
            if existing_record:
                raise UserError(_("A record with the same branch and running state already exists."))
        res = super(HRTmsOpenClose, self).create(values)
        return res

    #def init(self):
    #    dat = self.env['hr.opening.closing'].sudo().search([])
    #    for rec in dat:
    #        if rec.branch_id and rec.open_periode_from and rec.open_periode_to:
    #            br = self.env['res.branch'].sudo().search([('id','=',rec.branch_id.id)])
    #            #rec.name = br.name + '/' +str(datetime.strptime(str(rec.open_periode_from), "%d-%m-%Y").date())+'-'+str(datetime.strptime(str(rec.open_periode_to), "%d-%m-%Y").date())
    #            if br:
    #                rec.write({'name': br.name + '/' + str((datetime.strptime(str(rec.open_periode_from), "%Y-%m-%d").date()).strftime('%d-%m-%Y'))+'-'+str((datetime.strptime(str(rec.open_periode_to), "%Y-%m-%d").date()).strftime('%d-%m-%Y'))})
    #                rec.env.cr.commit()

    def write(self, vals):
        for rec in self:
            if rec.branch_id and rec.open_periode_from and rec.open_periode_to:
                open_close_data = self.env['hr.opening.closing'].sudo().search([('id', '=', rec.id)])
                br = self.env['res.branch'].sudo().search([('id', '=', rec.branch_id.id)])

                # Convert date object to string before strptime
                date_string = open_close_data.open_periode_to.strftime("%Y-%m-%d")
                date_obj = datetime.strptime(date_string, "%Y-%m-%d")
                vals['name'] = date_obj.strftime("%B %Y") + ' | ' + br['name']
        res = super(HRTmsOpenClose, self).write(vals)

        # PENTING: Invalidate cache untuk SEMUA perubahan yang mempengaruhi button
        fields_to_check = ['state_process', 'processing_user_id', 'processing_start', 'isopen']

        if any(field in vals for field in fields_to_check):
            # Invalidate computed field
            self.invalidate_recordset([
                'state_process',
                'processing_user_id',
                'processing_start',
                'isopen',
                'show_process_button'  # ← Computed field
            ])

            _logger.debug(f"Cache invalidated for record {self.ids}")

        return res

    def compute_concate(self):
        print("MULAI CONCATE")
        recompute_tms = self.env['hr.tmsentry.summary'].sudo().search([])
        for record in recompute_tms:
            print(record.periode_id.name + str(record.date_from) + str(record.date_to), "ini yang baru")
            record.periode_from_to = record.periode_id.name + " | " + str(record.date_from) + " | " + str(record.date_to)

    def action_reproses(self):
        """
        Process dengan validasi concurrent access di method
        Button tetap muncul, validasi saat diklik
        """
        self.ensure_one()

        _logger.info(
            f"[REPROSES] User {self.env.user.name} (ID: {self.env.user.id}) "
            f"clicked Process button for record {self.id}"
        )

        # Validasi 1: Cek state done
        if self.state_process == 'done':
            raise UserError(_("Cannot process: This period is already closed."))

        # Validasi 2: Cek state running
        if self.state_process != 'running':
            raise UserError(_(
                "Cannot process: Record status is '%s'.\n\n"
                "Please refresh the page."
            ) % dict(self._fields['state_process'].selection).get(self.state_process))

        # Lock row untuk prevent concurrent access
        try:
            self.env.cr.execute(
                """
                SELECT id, processing_user_id
                FROM hr_opening_closing
                WHERE id = %s
                    FOR UPDATE NOWAIT
                """,
                (self.id,),
                log_exceptions=False
            )
        except OperationalError as e:
            if e.pgcode == errorcodes.LOCK_NOT_AVAILABLE:
                # Row sedang di-lock user lain
                raise UserError(_(
                    "This record is currently locked by another user.\n\n"
                    "Please wait a moment and try again."
                ))
            elif e.pgcode == errorcodes.SERIALIZATION_FAILURE:
                # Concurrent modification detected
                raise UserError(_(
                    "This record was just modified by another user.\n\n"
                    "Please refresh the page and try again."
                ))
            else:
                _logger.error(f"Database lock error: {str(e)}")
                raise UserError(_(
                    "Unable to acquire lock on this record.\n\n"
                    "Please try again or contact administrator."
                ))

        # Refresh data dari database setelah dapat lock
        self.invalidate_recordset(['processing_user_id', 'processing_start'])
        # self.refresh()

        # Validasi 3: Cek apakah sedang diproses user lain
        if self.processing_user_id:
            # Hitung elapsed time
            if self.processing_start:
                elapsed = fields.Datetime.now() - self.processing_start
                minutes = int(elapsed.total_seconds() / 60)
                time_info = f"({minutes} minutes ago)"
            else:
                time_info = ""

            raise UserError(_(
                "❌ Store Procedure sedang dijalankan oleh user lain.\n\n"
                "Processing by: %s\n"
                "Started: %s %s\n\n"
                "Please wait until the process completes and try again."
            ) % (
                                self.processing_user_id.name,
                                self.processing_start.strftime('%Y-%m-%d %H:%M:%S') if self.processing_start else 'N/A',
                                time_info
                            ))

        # Set processing flag
        self.write({
            'processing_user_id': self.env.user.id,
            'processing_start': fields.Datetime.now(),
        })

        # COMMIT immediately agar user lain langsung tahu
        self.env.cr.commit()

        _logger.info(
            f"[REPROSES] Record {self.id} locked by user {self.env.user.name}"
        )

        # Post message to chatter
        body = _('Re-Process Period started by %s') % self.env.user.name
        self.message_post(body=body)

        # Execute stored procedure dengan error handling
        success = False
        error_message = None

        try:
            # Prepare parameters
            period_id = self.id
            area_id = self.area_id.id if self.area_id else None
            branch_id = self.branch_id.id if self.branch_id else None

            _logger.info(
                f"[REPROSES] Calling stored procedure calculate_tms with params: "
                f"period_id={period_id}, area_id={area_id}, branch_id={branch_id}"
            )

            # Execute stored procedure (ini yang lama ~2 menit)
            self.env.cr.execute(
                "CALL calculate_tms(%s, %s, %s)",
                (period_id, area_id, branch_id)
            )

            # Recompute summary
            self.recompute_tms_summary()

            # Update flags
            self.isopen = True
            self.state_process = "running"

            # Compute concatenate
            self.compute_concate()

            success = True
            _logger.info(f"[REPROSES] Record {self.id} processed successfully")

        except OperationalError as e:
            error_message = str(e)
            if e.pgcode == errorcodes.SERIALIZATION_FAILURE:
                error_message = "Concurrent modification detected during processing."
            _logger.error(f"[REPROSES] Database error: {error_message}", exc_info=True)

        except Exception as e:
            error_message = str(e)
            _logger.error(f"[REPROSES] Error executing stored procedure: {error_message}", exc_info=True)

        # Clear processing flag
        try:
            if success:
                self.write({
                    'processing_user_id': False,
                    'processing_start': False,
                })

                # TAMBAHKAN INI: Force invalidate cache untuk computed field
                self.invalidate_recordset([
                    'state_process',
                    'processing_user_id',
                    'processing_start',
                    'show_process_button'  # ← PENTING!
                ])

                body = _('Re-Process Period completed successfully by %s') % self.env.user.name
                self.message_post(body=body)

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Process completed successfully.'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                # Clear flag dan raise error
                self.write({
                    'processing_user_id': False,
                    'processing_start': False,
                })

                # Invalidate cache
                self.invalidate_recordset([
                    'processing_user_id',
                    'processing_start',
                    'show_process_button'
                ])

                body = _('Re-Process Period failed: %s') % error_message
                self.message_post(body=body)

                raise UserError(_(
                    "Failed to execute the stored procedure.\n\n"
                    "Error: %s\n\n"
                    "Please contact your administrator if this problem persists."
                ) % error_message)

        except UserError:
            raise
        except Exception as cleanup_error:
            _logger.error(f"Failed to cleanup processing flag: {str(cleanup_error)}")
            if not success:
                raise UserError(_(
                    "Process failed and unable to reset processing state.\n\n"
                    "Please contact your administrator."
                ))

    def recompute_tms_summary(self):
        for rec in self:
            tms_summary_data = self.env['hr.tmsentry.summary'].sudo().search([
                ('periode_id', '=', rec.id),
                ('area_id', '=', rec.area_id.id),
                ('branch_id', '=', rec.branch_id.id)
            ])

            employee_ids = tms_summary_data.mapped('employee_id.id')

            hr_employee_data = self.env['hr.employee'].sudo().search([
                ('id', 'in', employee_ids)
            ])

            employee_dict = {emp.id: emp for emp in hr_employee_data}
            
            for tsd in tms_summary_data:
                employee = employee_dict.get(tsd.employee_id.id)
                if employee:
                    tsd.ot = employee.allowance_ot
                    tsd.ot_flat = employee.allowance_ot_flat
                    tsd.night_shift = employee.allowance_night_shift

    def action_opening_periode(self):
        for data in self:
            if not data.open_periode_from or not data.open_periode_to:
                raise UserError(
                    "The 'Periode From' and 'Periode To' fields are required. Please enter values for both fields."
                )

            ''' buat pesan pada chatter 
            ketika button opening process di klik '''
            body = _('Process Period: %s' % self.state_process)
            data.message_post(body=body)

            # period_id = data.id
            # area_id = data.area_id
            # branch_id = data.branch_id
            #
            # ''' validasi : Seluruh employee group yg sesuai area & branch nya sama dengan
            # area & branch dari proses open period yg sedang dijalankan,
            # harus sudah berstatus approve '''
            # employee_group = self.env['hr.empgroup'].sudo().search([
            #     ('area_id', '=', area_id.id),
            #     ('branch_id', '=', branch_id.id),
            #     ('state', '!=', 'approved')
            # ])
            #
            # if len(employee_group) > 1:
            #     raise UserError('Ensure all employee groups have been approved.')

            data.isopen = True
            data.state_process = "running"

    def action_closing_periode(self):
        for data in self:
            # summary = self.env['hr.tmsentry.summary'].search([('periode_id','=',data.id)])
            # import pdb
            # pdb.set_trace()
            # for record in summary:
            #     record.write({'state': 'done'})
            #     attendances = self.env['sb.tms.tmsentry.details'].search([('tmsentry_id','=',record.id)])
            #     for attn in attendances:
            #         attn.write({'status': 'done'})
            #     permissions = self.env['hr.permission.entry'].search([('periode_id','=',record.periode_id.id)])
            #     for perm in permissions:
            #         # perm.write({'permission_status': 'done'})
            #         perm.write({'permission_status': 'close'})
            #     overtime = self.env['hr.overtime.planning'].search([('periode_id','=',data.id)])
            #     for ot in overtime:
            #         ot.write({'state': 'done'})

            data.write({'state_process': 'done'})
            data.write({'isopen': 0}) # isopen = False

            # search_permission = self.env['hr.permission.entry'].sudo().search([
            #     ('permission_date_from', '>=', data.open_periode_from),
            #     ('permission_date_To', '<=', data.open_periode_to),
            #     ('branch_id', '=', data.branch_id.id),
            #     ('area_id', '=', data.area_id.id),
            #     ('permission_status', '=', 'approved')
            # ])
            #
            # # Update status di permission entry = close (done)
            # search_permission.write({'permission_status': 'done'})

    def transfer_payroll(self):
        pass
        
        # for data in self:
        #     searchpermission = self.env['hr.permission.entry'].sudo().search([
        #         ('permission_date_from', '>=', data.open_periode_from),
        #         ('permission_date_To', '<=', data.open_periode_to),
        #         ('branch_id', '=', data.branch_id.id),
        #         ('area_id', '=', data.area_id.id)
        #     ])

        #     for permission in searchpermission:
        #         permission.permission_status = 'done'

        # for alldata in self:
        #     # if not alldata.close_periode_from or not alldata.close_periode_to:
        #     #     raise UserError("Please Input Periode From And To First")
        #     carisummary = self.env['hr.tmsentry.summary'].sudo().search([
        #         ('date_from', '=', alldata.open_periode_from),
        #         ('date_to', '<=', alldata.open_periode_to),
        #         ('branch_id', '=', alldata.branch_id.id)
        #     ])
        #     for allsummary in carisummary:
        #         if allsummary.state != 'transfer_payroll':
        #             raise UserError('The Closing process cannot be carried out because there still transaction that have not been transffered to payroll')
        #         else:
        #             allsummary.write({'state': 'done'})
        #     return

    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        
        if view_type in ('tree', 'form'):
            group_name = self.env['res.groups'].search([('name','in',['User TMS','HRD CA'])])
            cekgroup = self.env.user.id in group_name.users.ids
            if cekgroup:
                for node in arch.xpath("//field"):
                    node.set('readonly', 'True')
                for node in arch.xpath("//button"):
                    node.set('invisible', 'True')
                for node in arch.xpath("//tree"):
                    node.set('create', '0')
                for node in arch.xpath("//form"):
                    node.set('create', '0')
        return arch, view