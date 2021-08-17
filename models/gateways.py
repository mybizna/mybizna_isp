from odoo import models, fields


class Gateways(models.Model):

    _name = 'mybizna.isp.gateways'
    _rec_name = 'title'

    title = fields.Char('Title', required=True)
    username = fields.Char('Username', required=True)
    password = fields.Char('Password', required=True)
    database = fields.Char('Database', required=True)
    ip_address = fields.Char('IP Address', required=True)
    port = fields.Integer('Port', required=True)
    type = fields.Selection(
        [('freeradius', 'Freeradius')], 'Type', default='freeradius')
    published = fields.Boolean('Published')
    by_sql_file = fields.Boolean('FreeRadius Updates By File')
