from datetime import datetime
from random import randint, random
from odoo import models, fields
import mysql.connector as mysql

import logging, requests


class Packages(models.Model):

    _name = 'mybizna.isp.packages'
    _rec_name = 'title'

    title = fields.Char('Title', required=True)
    description = fields.Text('Description', required=True)
    gateway_id = fields.Many2one(
        'mybizna.isp.gateways', string='Gateway')
    billing_cycle_id = fields.Many2one(
        'mybizna.isp.billing_cycle', string='Billing Cycle')
    currency_id = fields.Many2one(
        'res.currency', string='Currency')
    speed = fields.Char('Speed', required=True)
    speed_type = fields.Selection(
        [('k', 'Kilobyte'), ('M', 'MegaByte')], 'Direction', required=True, default='M')
    amount = fields.Monetary('amount', required=True)
    published = fields.Boolean('Published')

    packages_setupitems_ids = fields.One2many('mybizna.isp.packages_setupitems', 'package_id',
                                              'Package Setup Items',
                                              track_visibility='onchange')

    def processPackages(self):

        packages = self.env['mybizna.isp.packages'].search([
            ("published", "=", True),
        ])

        for package in packages:

            try:

                speed = package.speed + package.speed_type
                double_speed = (package.speed * 2) + package.speed_type

                microtik_limit = ''+speed+'/'+speed+' '+double_speed + \
                    '/'+double_speed+' '+speed+'/'+speed+' 40/40'

                actions = [
                    "DELETE FROM radgroupcheck WHERE groupname='" +
                    speed + "' and attribute='Framed-Protocol'",
                    'insert into radgroupcheck (groupname,attribute,op,value) values ("' +
                    speed + '","Framed-Protocol","==","PPP");',
                    "DELETE FROM radgroupreply WHERE groupname='" +
                    speed + "' and attribute='Framed-Pool'",
                    'insert into radgroupreply (groupname,attribute,op,value) values ("' +
                    speed + '","Framed-Pool","=","' + speed + '_pool");',
                    "DELETE FROM radgroupreply WHERE groupname='" +
                    speed + "' and attribute='Mikrotik-Rate-Limit'",
                    'insert into radgroupreply (groupname,attribute,op,value) values ("' +
                    speed + '","Mikrotik-Rate-Limit","=","' + microtik_limit + '");',
                    "DELETE FROM radusergroup WHERE username='" +
                    speed + "_Profile' and groupname='" + speed + "'",
                    'insert into radusergroup (username,groupname,priority) values ("' +
                    speed + '_Profile","' + speed + '",10);',
                ]

                if package.gateway.by_sql_file:

                    for action in actions:
                        r=requests.post('http://' + package.gateway_id.ip_address + '/isp/query.php', data = {'query': action})

                        _logger = logging.getLogger(__name__)
                        _logger.error(r.content)                        
                else:
                    db = mysql.connect(
                        host=package.gateway_id.ip_address,
                        user=package.gateway_id.username,
                        passwd=package.gateway_id.password,
                        database=package.gateway_id.database
                    )

                    cursor = db.cursor()

                    for action in actions:
                        cursor.execute(action)
                        db.commit()

            except:
                pass
