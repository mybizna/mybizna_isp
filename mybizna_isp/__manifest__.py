# -*- coding: utf-8 -*-
{
    'version': '0.2',
    'name': "ISP Manager",

    'summary': """
        Internet Service Provider App for managing connections.""",

    'description': """
        Internet Service Provider App for managing connections.
    """,

    'author': "Mybizna",
    'website': "http://www.mybizna.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounts',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    'images': ['static/images/banner.png', 'static/description/icon.png',  'static/images/thubmnail1.png'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/main_menu.xml',
        'views/billing_cycle_view.xml',
        'views/billing_items_view.xml',
        'views/billing_view.xml',
        'views/connections_view.xml',
        'views/gateways_view.xml',
        'views/packages_setupitems_view.xml',
        'views/packages_view.xml',
        'demo/demo.xml',
        'demo/cron.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
