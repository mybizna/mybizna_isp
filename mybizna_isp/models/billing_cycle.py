from odoo import models, fields


class BillingCycle(models.Model):

    _name = 'mybizna.isp.billing_cycle'
    _rec_name = 'title'

    title = fields.Char('Title', required=True)
    description = fields.Text('Description', required=True)
    duration = fields.Integer('Duration', required=True)
    duration_type = fields.Selection(
        [ ('days', 'Day'), ('weeks', 'Week'), ('months', 'Month')], 'Duration Type', required=True, default='day')
    published = fields.Boolean('Published')
