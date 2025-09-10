from odoo import fields, models, api,  _, Command
from odoo.exceptions import ValidationError, UserError
import logging

class SbBreakMaster (models.Model):
    _name = 'sb.break.master'

    branch_id = fields.Many2one('res.branch', string='Business Unit')
    break_from = fields.Float('Break From')
    break_to = fields.Float('Break To')
    is_active = fields.Boolean('Active')

    @api.constrains('break_from','break_to')
    def _break_time_check(self):
        for rec in self:
            if rec.break_from > rec.break_to:
                raise ValidationError("Break From must be earlier than Break To.")

    @api.constrains('break_from','break_to','branch_id','is_active')
    def _overlap_check(self):
        for rec in self:
            if rec.branch_id and rec.is_active :
                overlaps = self.env['sb.break.master'].search([
                    ('id', '!=', rec.id),
                    ('branch_id', '=', rec.branch_id.id),
                    ('is_active', '=', True),
                    ('break_from', '<', rec.break_to),
                    ('break_to', '>', rec.break_from),
                ], limit=1)
                if overlaps:
                    raise ValidationError(_(
                        "Break time periods cannot overlap: \n"
                        "Your range: %s - %s \n"
                        "Existing range: %s - %s \n"
                        "Branch: %s"
                    ) % (
                        rec.break_from,
                        rec.break_to,
                        overlaps.break_from,
                        overlaps.break_to,
                        rec.branch_id.name,
                    ))
