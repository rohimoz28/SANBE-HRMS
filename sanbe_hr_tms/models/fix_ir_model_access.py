from odoo import fields, models, api


class IrModelAccess(models.Model):
    _name = 'fix.ir.model.access'
    _description = 'Fix Ir Model Access'
    _order = 'model_id,group_id,name,id'
    _allow_sudo_commands = False

    name = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True, help='If you uncheck the active field, it will disable the ACL without deleting it (if you delete a native ACL, it will be re-created when you reload the module).')
    model_id = fields.Many2one('ir.model', string='Model', required=True, index=True, ondelete='cascade')
    group_id = fields.Many2one('res.groups', string='Group', ondelete='restrict', index=True)
    perm_read = fields.Boolean(string='Read Access')
    perm_write = fields.Boolean(string='Write Access')
    perm_create = fields.Boolean(string='Create Access')
    perm_unlink = fields.Boolean(string='Delete Access')
