from odoo import models, fields


class Billing(models.Model):

    _name = 'mybizna.isp.billing'
    _rec_name = 'title'

    connection_id = fields.Many2one(
        'mybizna.isp.connections', string='Connections')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    title = fields.Char('Title', required=True)
    description = fields.Text('Description', required=True)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    is_paid = fields.Boolean('Is Paid', default=False)


    billing_items_ids = fields.One2many('mybizna.isp.billing_items', 'billing_id',
                                        'Billing Items',
                                        track_visibility='onchange')


    def generate_invoice(self, billing):

        invoice_line_ids = []

        items = self.env['mybizna.isp.billing_items'].search([("billing_id.id", "=", billing.id)])

        for item in items:

            invoice_line_ids.append((0, 0, {
                    'name': item.title,
                    'quantity': 1,
                    'price_unit': item.amount,
                    'price_subtotal' : item.amount,
                    'account_id': 21,
            }))

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': billing.connection_id.partner_id.id,
            'user_id': self.env.user.id,
            'invoice_line_ids': invoice_line_ids,
        })


        invoice.action_post()

        self.reconcile_invoice(invoice)



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

    def processBilling(self):

        billings = self.env['mybizna.isp.billing'].search([
                ("is_paid", "=", True),
                ("invoice_id.payment_state", "=", 'paid'),
        ])

        for billing in billings:
            billing.write({'is_paid':True})
            billing.connection_id.write({
                'is_paid':True
            })

            self.env.cr.commit()

            billing.connection_id.addToRadius(billing.connection_id.id)
       