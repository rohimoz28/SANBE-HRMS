from odoo import fields, models, api

class SbTaxYearly (models.Model):
    _name = 'sb.tax.yearly'
    _description = 'Tax Yearly'

    tax_statutory_ids = fields.One2many('sb.tax.statutory', 'tax_yearly_id', string='Tax Statutory IDs')
    tax_fomula_ids = fields.One2many('sb.tax.formula', 'tax_yearly_id', string='Tax Fomula IDs')
    effective_date = fields.Date(string='Effective Date From')
    tk0 = fields.Monetary('TK0', currency_field='currency_id')
    tk1 = fields.Monetary('TK1', currency_field='currency_id')
    tk2 = fields.Monetary('TK2', currency_field='currency_id')
    tk3 = fields.Monetary('TK3', currency_field='currency_id')
    k0 = fields.Monetary('K0', currency_field='currency_id')
    k1 = fields.Monetary('K1', currency_field='currency_id')
    k2 = fields.Monetary('K2', currency_field='currency_id')
    k3 = fields.Monetary('K3', currency_field='currency_id')
    positional_allowance = fields.Float('Positional Allowance')
    # or_max = fields.Float('Or Max')
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env['res.currency'].search([('name', '=', 'IDR')], limit=1).id
    )
    or_max = fields.Monetary('Or Max', currency_field='currency_id')
    
    def unlink(self):
        return super(SbTaxYearly, self).unlink()

class SbTaxStatutory (models.Model):
    _name = 'sb.tax.statutory'
    _description = 'Tax Statutory'

    tax_yearly_id = fields.Many2one('sb.tax.yearly', string='Tax Yearly ID', ondelete='cascade')
    currency_id = fields.Many2one(related='tax_yearly_id.currency_id', store=True)
    s_from = fields.Monetary('From', currency_field='currency_id')
    s_to = fields.Monetary('To', currency_field='currency_id')
    s_deduct = fields.Float('Deduct')

class SbTaxFormula (models.Model):
    _name = 'sb.tax.formula'
    _description = 'Tax Formula'

    tax_yearly_id = fields.Many2one('sb.tax.yearly', string='Tax Yearly ID', ondelete='cascade')
    currency_id = fields.Many2one(related='tax_yearly_id.currency_id', store=True)
    f_from = fields.Monetary('From', currency_field='currency_id')
    f_to = fields.Monetary('To', currency_field='currency_id')
    f_factor_x = fields.Float('Faktor X')
    f_formula = fields.Text('Formula')
