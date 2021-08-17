from odoo import models, fields


class ConnectionsSetupitems(models.Model):

    _name = 'mybizna.isp.connections_setupitems'
    _rec_name = 'title'

    title = fields.Char('Title', required=True)
    description = fields.Text('Description', required=True)
    connection_id = fields.Many2one('mybizna.isp.connections', string='Connections')
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount = fields.Monetary('amount', required=True)
