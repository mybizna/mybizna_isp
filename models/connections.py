from random import random
from odoo import models, fields, api
import mysql.connector as mysql

import logging
import datetime, requests
from dateutil.relativedelta import *


class Connections(models.Model):

    _name = 'mybizna.isp.connections'
    _rec_name = 'username'

    package_id = fields.Many2one('mybizna.isp.packages', string='Package')
    partner_id = fields.Many2one('res.partner', 'Partner', ondelete="cascade")
    invoice_id = fields.Many2one('account.move', string='Invoice')
    username = fields.Char('Username', required=True)
    password = fields.Char('Password', required=True)
    expiry_date = fields.Date('Expiry Date')
    billing_date = fields.Date('Billing Date')
    params = fields.Text('Params Text')
    is_setup = fields.Boolean('Is Setup', default=False)
    is_paid = fields.Boolean('Is Paid', default=False)
    status = fields.Selection(
        [('new', 'New'), ('active', 'Active'), ('inactive', 'In Active'), ('closed', 'Closed')], 'Status', required=True, default='new')

    connections_setupitems_ids = fields.One2many('mybizna.isp.connections_setupitems', 'connection_id',
                                                 'Setup Items',
                                                 track_visibility='onchange')

    connections_invoices_ids = fields.One2many('mybizna.isp.connections_invoices', 'connection_id',
                                               'Invoices',
                                               track_visibility='onchange')

    def _is_new(self):

        if self.id:
            self.is_new = True
        else:
            self.is_new = False

    @api.model
    def create(self, values):

        res = super(Connections, self).create(values)

        items = self.env['mybizna.isp.packages_setupitems'].search([
            ("package_id.id", "=", res.package_id.id),
            ("published", "=", 1),
        ])

        for item in items:

            objects = {
                'title': item.title,
                'description': item.description,
                'currency_id': item.currency_id.id,
                'connection_id': res.id,
                'amount': item.amount,
            }

            self.env['mybizna.isp.connections_setupitems'].create(
                objects)

        return res

    def generate_invoice(self):

        invoice_line_ids = []

        items = self.env['mybizna.isp.connections_setupitems'].search(
            [("connection_id.id", "=", self.id)])

        if not len(items):
            items = self.env['mybizna.isp.packages_setupitems'].search([
                ("package_id.id", "=",  self.package_id.id),
                ("published", "=", 1),
            ])

            for item in items:

                objects = {
                    'title': item.title,
                    'description': item.description,
                    'currency_id': item.currency_id.id,
                    'connection_id': self.id,
                    'amount': item.amount,
                }

                self.env['mybizna.isp.connections_setupitems'].create(
                    objects)

        for item in items:

            invoice_line_ids.append((0, 0, {
                'name': item.title,
                'quantity': 1,
                'price_unit': item.amount,
                'price_subtotal': item.amount,
                'account_id': 21,
            }))

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'user_id': self.env.user.id,
            'invoice_line_ids': invoice_line_ids,
        })

        invoice.action_post()

        self.reconcile_invoice(invoice)

        self.env['mybizna.isp.connections_invoices'].create(
            {'connection_id': self.id, 'invoice_id': invoice.id}
        )

        return self.write({'is_setup': True, 'invoice_id': invoice.id})

    def update_radius(self):
        self.addToRadius(self)
        self.processAllConnections()
        self.processNewConnections()
        self.env.get('mybizna.isp.packages').processPackages()


    def reconcile_invoice(self, invoice):

        if invoice.state != 'posted' \
                or invoice.payment_state not in ('not_paid', 'partial') \
                or not invoice.is_invoice(include_receipts=True):
            return False

        pay_term_lines = invoice.line_ids\
            .filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))

        domain = [
            ('account_id', 'in', pay_term_lines.account_id.ids),
            ('move_id.state', '=', 'posted'),
            ('partner_id', '=', invoice.commercial_partner_id.id),
            ('reconciled', '=', False),
            '|', ('amount_residual', '!=',
                  0.0), ('amount_residual_currency', '!=', 0.0),
        ]

        if invoice.is_inbound():
            domain.append(('balance', '<', 0.0))
        else:
            domain.append(('balance', '>', 0.0))

        for line in self.env['account.move.line'].search(domain):

            lines = self.env['account.move.line'].browse(line.id)
            lines += invoice.line_ids.filtered(
                lambda line: line.account_id == lines[0].account_id and not line.reconciled)
            lines.reconcile()

    def processExpiry(self):

        connections = self.env['mybizna.isp.connections'].search([
            ("status", "=", 'active'),
            ("is_paid", "=", True),
            ('expiry_date', '<=',
             ((datetime.date.today()).strftime('%Y-%m-%d')))
        ])

        packages = self.env['mybizna.isp.packages'].search(
            [], order="amount asc")

        for connection in connections:

            connection.write({
                'is_paid': False,
                'package_id': packages[0].id,
            })

            self.env.cr.commit()

            connection.addToRadius(connection)

    def prepareBilling(self):

        gap_days = 5

        connections = self.env['mybizna.isp.connections'].search([
            ("status", "=", 'active'),
            ('billing_date', '<=', ((datetime.date.today() +
                                     relativedelta(days=gap_days)).strftime('%Y-%m-%d')))
        ])

        for connection in connections:

            kwargs = self.getDateKwargs(connection)

            curr_billing_date = connection.billing_date if connection.billing_date else datetime.date.today()
            start_date = (curr_billing_date).strftime('%Y-%m-%d')
            end_date = (curr_billing_date + relativedelta(**kwargs)
                        ).strftime('%Y-%m-%d')
            billing_date = end_date

            connection.write({
                'billing_date': billing_date,
            })

            self.env.cr.commit()

            billing = self.env['mybizna.isp.billing'].create({
                'connection_id': connection.id,
                'title': connection.package_id.title,
                'description': connection.package_id.title,
                'start_date': start_date,
                'end_date': end_date,
            })

            self.env['mybizna.isp.billing_items'].create({
                'title': connection.package_id.title,
                'description': connection.package_id.title,
                'billing_id': billing.id,
                'amount': connection.package_id.amount,
            })

            self.env['mybizna.isp.billing'].generate_invoice(billing)

    def processNewConnections(self):

        connections = self.env['mybizna.isp.connections'].search([
            ("status", "=", 'new'),
            ('invoice_id.payment_state', '=', 'paid')
        ])

        for connection in connections:

            kwargs = self.getDateKwargs(connection)

            billing_cycle = connection.package_id.billing_cycle_id

            connection.write({
                'is_paid': True,
                'status': 'active',
                'billing_date': ((datetime.date.today() + relativedelta(kwargs)).strftime('%Y-%m-%d')),
            })

            self.env.cr.commit()

            connection.addToRadius(connection)

    def processAllConnections(self):
        connections = self.env['mybizna.isp.connections'].search([
            ("status", "=", 'active'),
            ('invoice_id.payment_state', '=', 'paid')
        ])

        for connection in connections:

            connection.addToRadius(connection)

    def getDateKwargs(self, connection):

        frequencies = ["days", "weeks", "months"]
        duration_type = connection.package_id.billing_cycle_id.duration_type
        duration = connection.package_id.billing_cycle_id.duration

        kwargs = {"months": 1}

        if duration_type in frequencies:
            kwargs = {duration_type: duration}

        return kwargs

        '''
        https://systemzone.net/freeradius-user-profile-configuration-for-mikrotik-router/

        SETUP PACKAGES

        insert into radgroupcheck (groupname,attribute,op,value) values ("32k","Framed-Protocol","==","PPP");
        insert into radgroupcheck (groupname,attribute,op,value) values ("512k","Framed-Protocol","==","PPP");
        insert into radgroupcheck (groupname,attribute,op,value) values ("1M","Framed-Protocol","==","PPP");
        insert into radgroupcheck (groupname,attribute,op,value) values ("2M","Framed-Protocol","==","PPP");

        insert into radgroupreply (groupname,attribute,op,value) values ("32k","Framed-Pool","=","32k_pool");
        insert into radgroupreply (groupname,attribute,op,value) values ("512k","Framed-Pool","=","512k_pool");
        insert into radgroupreply (groupname,attribute,op,value) values ("1M","Framed-Pool","=","1M_pool");
        insert into radgroupreply (groupname,attribute,op,value) values ("2M","Framed-Pool","=","2M_pool");

        insert into radgroupreply (groupname,attribute,op,value) values ("32k","Mikrotik-Rate-Limit","=","32k/32k 64k/64k 32k/32k 40/40");
        insert into radgroupreply (groupname,attribute,op,value) values ("512k","Mikrotik-Rate-Limit","=","512k/512k 1M/1M 512k/512k 40/40");
        insert into radgroupreply (groupname,attribute,op,value) values ("1M","Mikrotik-Rate-Limit","=","1M/1M 2M/2M 1M/1M 40/40");
        insert into radgroupreply (groupname,attribute,op,value) values ("2M","Mikrotik-Rate-Limit","=","2M/2M 4M/4M 2M/2M 40/40");

        insert into radusergroup (username,groupname,priority) values ("32k_Profile","32k",10);
        insert into radusergroup (username,groupname,priority) values ("512k_Profile","512k",10);
        insert into radusergroup (username,groupname,priority) values ("1M_Profile","1M",10);
        insert into radusergroup (username,groupname,priority) values ("2M_Profile","2M",10);

        CREATE USERS

        insert into radcheck (username,attribute,op,value) values ("free","Cleartext-Password",":=","passme");
        insert into radcheck (username,attribute,op,value) values ("bob","Cleartext-Password",":=","passme");
        insert into radcheck (username,attribute,op,value) values ("alice","Cleartext-Password",":=","passme");
        insert into radcheck (username,attribute,op,value) values ("tom","Cleartext-Password",":=","passme");

        insert into radcheck (username,attribute,op,value) values ("free","User-Profile",":=","32k_Profile");
        insert into radcheck (username,attribute,op,value) values ("bob","User-Profile",":=","512k_Profile");
        insert into radcheck (username,attribute,op,value) values ("alice","User-Profile",":=","1M_Profile");
        insert into radcheck (username,attribute,op,value) values ("tom","User-Profile",":=","2M_Profile");

        '''

    def addToRadius(self, connection):

        speed = connection.package_id.speed + connection.package_id.speed_type

        actions = [
            "DELETE FROM radcheck WHERE username='" +
            connection.username + "' and attribute='Cleartext-Password'",
            'insert into radcheck (username,attribute,op,value) values ("' +
            connection.username + '","Cleartext-Password",":=","' + connection.password + '");',
            "DELETE FROM radcheck WHERE username='" +
            connection.username + "' and attribute='User-Profile'",
            'insert into radcheck (username,attribute,op,value) values ("' +
            connection.username + '","User-Profile",":=","' + speed + '_Profile");',
        ]


        try:
            if connection.gateway.by_sql_file:

                # current date and time
                for action in actions:
                    r=requests.post('http://' + connection.package_id.gateway_id.ip_address + '/isp/query.php', data = {'query': action})

                    _logger = logging.getLogger(__name__)
                    _logger.error(r.content)
                
            else:

                db = mysql.connect(
                    host=connection.package_id.gateway_id.ip_address,
                    user=connection.package_id.gateway_id.username,
                    passwd=connection.package_id.gateway_id.password,
                    database=connection.package_id.gateway_id.database
                )

                cursor = db.cursor()

                for action in actions:
                    cursor.execute(action)
                    db.commit()

        except:
            pass
