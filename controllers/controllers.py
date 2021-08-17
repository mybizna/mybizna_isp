# -*- coding: utf-8 -*-
# from odoo import http


# class MybiznaIsp(http.Controller):
#     @http.route('/mybizna_isp/mybizna_isp/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mybizna_isp/mybizna_isp/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mybizna_isp.listing', {
#             'root': '/mybizna_isp/mybizna_isp',
#             'objects': http.request.env['mybizna_isp.mybizna_isp'].search([]),
#         })

#     @http.route('/mybizna_isp/mybizna_isp/objects/<model("mybizna_isp.mybizna_isp"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mybizna_isp.object', {
#             'object': obj
#         })
