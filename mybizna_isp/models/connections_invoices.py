from odoo import models, fields


class ConnectionsInvoice(models.Model):

    _name = 'mybizna.isp.connections_invoices'
    _rec_name = 'connection_id'

    connection_id = fields.Many2one('mybizna.isp.connections', string='Connections')
    invoice_id = fields.Many2one('account.move', string='Invoice')
