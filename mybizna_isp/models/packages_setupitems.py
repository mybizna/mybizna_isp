from odoo import models, fields


class PackagesSetupitems(models.Model):

    _name = 'mybizna.isp.packages_setupitems'
    _rec_name = 'title'

    title = fields.Char('Title', required=True)
    description = fields.Text('Description', required=True)
    package_id = fields.Many2one('mybizna.isp.packages', string='Packages')
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount = fields.Monetary('amount', required=True)
    published = fields.Boolean('Published')
