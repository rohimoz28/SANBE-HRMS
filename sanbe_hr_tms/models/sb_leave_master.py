from odoo import fields, models, api,  _, Command
from odoo.exceptions import ValidationError, UserError
import logging

class SbLeaveMaster(models.Model):
    _name = 'sb.leave.master'

    area_id = fields.Many2one('res.territory', string='Area')
    branch_ids = fields.Many2many('res.branch', 'res_branch_rel', string='AllBranch', compute='_isi_semua_branch',
                                  store=False)
    branch_id = fields.Many2one('res.branch', string='Business Unit', domain="[('id','in',branch_ids)]")
    name = fields.Char('Name')
    code = fields.Char('Code')
    is_deduct_balance = fields.Boolean('Potong Saldo Cuti')
    days = fields.Float('Days')

    @api.depends('area_id')
    def _isi_semua_branch(self):
        for allrecs in self:
            databranch = []
            for allrec in allrecs.area_id.branch_id:
                mybranch = self.env['res.branch'].search([('name', '=', allrec.name)], limit=1)
                databranch.append(mybranch.id)
            allbranch = self.env['res.branch'].sudo().search([('id', 'in', databranch)])
            allrecs.branch_ids = [Command.set(allbranch.ids)]
    
    @api.constrains('code')
    def duplicate_code_check(self):
        for rec in self:
            duplicate_code = self.search([
                ('id', '!=', rec.id),
                ('code','=',rec.code),
            ])
            if duplicate_code:
                raise ValidationError(f"Duplicate code found: {rec.code}.")
            