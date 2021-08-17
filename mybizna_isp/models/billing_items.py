from odoo import models, fields


class BillingItems(models.Model):

    _name = 'mybizna.isp.billing_items'
    _rec_name = 'billing_id'

    title = fields.Char('Title', required=True)
    billing_id = fields.Many2one(
        'mybizna.isp.billing', string='Billing')
    currency_id = fields.Many2one(
        'res.currency', string='Currency')
    amount = fields.Monetary('amount', required=True)    
    description = fields.Text('Description', required=True)
