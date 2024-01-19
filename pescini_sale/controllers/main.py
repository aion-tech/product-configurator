from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request
from odoo.exceptions import ValidationError
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi import FastAPI, HTTPException
from werkzeug.exceptions import Forbidden, NotFound
from odoo.addons.website.controllers.main import QueryURL
from datetime import datetime
from odoo.tools import lazy
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.payment import utils as payment_utils


pescini_api_router = APIRouter()
app = FastAPI()

class PesciniPosWebsiteSale(http.Controller):
    
    # Task PES-91
    @http.route(["/shop/clear"], type="json", auth="public", website=True, methods=['POST'], csrf=False)
    def clear_cart(self):               
        order = request.website.sale_get_order()
        if order:
            [line.unlink() for line in order.website_order_line]

        return request.redirect("/shop")
    
    # @http.route(["/quotation/cart/<int:quotation_id>"], type="http", auth="public", website=True)
    # def cart_redirect_from_quotation(self, quotation_id):
    #     order = request.env['sale.order'].sudo().browse(quotation_id)
    #     if not order:
    #         return False
    #     order.state = 'draft'

    #     import ipdb; ipdb.set_trace()  # noqa
        
    #     return request.redirect(order.get_portal_url())

    # # @http.route(['/quotation/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    # @http.route(['/quotation/shop/cart/<int:quotation_id>'], type='http', auth="public", website=True)
    # def quotation_cart_update(self, quotation_id):
    #     """
    #     This route is called :
    #         - When changing quantity from the cart.
    #         - When adding a product from the wishlist.
    #         - When adding a product to cart on the same page (without redirection).
    #     """
    #     quotation_id = request.env['sale.order'].sudo().browse(quotation_id)

    #     return http.request.render('pescini_sale.quotation_cart_main', {
    #         'quotation': quotation_id,
    #     })
    
    # @http.route(['/quotation/cart/update/<int:quotation_id>/<int:order_line_id>'], type='http', auth="public", website=True)
    # def quotation_cart_update_line(self, quotation_id, order_line_id):
    #     quotation_id = request.env['sale.order'].sudo().browse(quotation_id)
    #     if not quotation_id:
    #         return
    #     if not quotation_id.order_line:
    #         return
    #     for line in quotation_id.order_line:
    #         if line.id == order_line_id:
    #             line.unlink()
    #     return http.request.render('pescini_sale.quotation_cart_main', {
    #         'quotation': quotation_id,
    #     }) 
    
    # @http.route(['/quotation/cart/update'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    # def quotation_cart_update_from_lines(self, quotation_id, order_line_id, sign):        
    #     quotation_id = request.env['sale.order'].sudo().browse(quotation_id)
    #     if not quotation_id:
    #         return
    #     if not quotation_id.order_line:
    #         return
    #     line = request.env['sale.order.line'].sudo().browse(order_line_id)
    #     if not line:
    #         return
    #     price_unit = line.price_unit
    #     upd_qty = line.product_uom_qty + sign
    #     if upd_qty <= 0:
    #         raise ValidationError(f'The quantity for product: {line.product_id.name} cannot be equal to 0')
    #     line.product_uom_qty += sign
    #     line.price_unit = price_unit
        
    #     return request.render('pescini_sale.quotation_cart_main', {
    #         'quotation': quotation_id,
    #     })

    
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.tools.json import scriptsafe as json_scriptsafe
class PesciniWebsiteSale(WebsiteSale):

    # Task PES-91
    @http.route(['/shop/cart/<int:quotation_id>'], type='http', auth="public", website=True, sitemap=False)
    def quotation_cart(self, access_token=None, revive='', quotation_id=False, **post):
        """
        Main cart management + abandoned cart revival
        access_token: Abandoned cart SO access token
        revive: Revival method when abandoned cart. Can be 'merge' or 'squash'
        """
        order = request.env['sale.order'].sudo().browse(quotation_id)
        
        if order and order.state != 'draft':
            request.session['sale_order_id'] = None
            order = request.env['sale.order'].sudo().browse(quotation_id)

        request.session['website_sale_cart_quantity'] = order.cart_quantity

        values = {}
        if access_token:
            abandoned_order = request.env['sale.order'].sudo().search([('access_token', '=', access_token)], limit=1)
            if not abandoned_order:  # wrong token (or SO has been deleted)
                raise NotFound()
            if abandoned_order.state != 'draft':  # abandoned cart already finished
                values.update({'abandoned_proceed': True})
            elif revive == 'squash' or (revive == 'merge' and not request.session.get('sale_order_id')):  # restore old cart or merge with unexistant
                request.session['sale_order_id'] = abandoned_order.id
                return request.redirect('/shop/cart')
            elif revive == 'merge':
                abandoned_order.order_line.write({'order_id': request.session['sale_order_id']})
                abandoned_order.action_cancel()
            elif abandoned_order.id != request.session.get('sale_order_id'):  # abandoned cart found, user have to choose what to do
                values.update({'access_token': abandoned_order.access_token})

        values.update({
            'website_sale_order': order,
            'date': fields.Date.today(),
            'suggested_products': [],
        })
        if order:
            values.update(order._get_website_sale_extra_values())
            order.order_line.filtered(lambda l: not l.product_id.active).unlink()
            values['suggested_products'] = order._cart_accessories()
            values.update(self._get_express_shop_payment_values(order))

        if post.get('type') == 'popover':
            # force no-cache so IE11 doesn't cache this XHR
            return request.render("website_sale.cart_popover", values, headers={'Cache-Control': 'no-cache'})

        return request.render("website_sale.cart", values)