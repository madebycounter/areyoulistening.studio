from lib import LastFM, ImageCache, Paypal, Database, Mailer, printmachine, webhooks, calculate_discount
from flask import Flask, render_template as render_template_raw, request, send_file, make_response, abort, Response, session, redirect, json
import io, os, re
import traceback
import time
import random
import base64

with open(os.environ['AYL_CONFIG'], 'r') as f:
    config = json.load(f)

with open(config['header_data'], 'r') as f:
    header_data = f.read()

if config['cache_buster'] == 'RANDOM':
    config['cache_buster'] = random.randint(10000, 99999)

mailer = Mailer(config['sendgrid']['api_key'])
lastfm = LastFM(config['lastfm']['api_key'], cache=config['lastfm']['cache'], use_api_for_top=config['lastfm']['use_api_for_top'],
                top_albums_file=config['lastfm']['top_albums_file'], cache_age=config['lastfm']['cache_age'])
imgcache = ImageCache(data=config['covers']['data_file'], dump=config['covers']['dump_dir'])
paypal = Paypal(config['paypal']['client_id'], config['paypal']['client_secret'], api_url=config['paypal']['api_url'])
database = Database(host=config['database']['host'], username=config['database']['username'],
                    password=config['database']['password'], database=config['database']['database'])

app = Flask(__name__, template_folder=config['templates_folder'])

# ERRORS
@app.errorhandler(400)
def error_400(e):
    return render_template('error.html', error_code=400), 400

@app.errorhandler(404)
def error_404(e):
    return render_template('error.html', error_code=404), 404

@app.errorhandler(500)
def error_500(e):
    database.add_tracking_event('ERROR', 'none', request, data='generic error')
    return render_template('error.html', error_code=500), 500

@app.errorhandler(Exception)
def handle_exception(e):
    embed = webhooks.build_generic_error('Server Error', '```%s```\nIP: `%s`\nURL: `%s`' % (traceback.format_exc(), request.remote_addr, request.path))
    webhooks.send_webhook(config['webhooks']['error'], embed)
    database.add_tracking_event('ERROR', 'none', request, data=str(e))
    return render_template('error.html', error_code=500), 500

# order_id, message, contact, base_url
def throw_checkout_error(request, msg, order_id, paypal_id, contact):
    database.set_order_status(order_id, 'ERROR')
    embed = webhooks.build_order_error(msg, order_id, paypal_id, contact, config['base_url'])
    webhooks.send_webhook(config['webhooks']['error'], embed)
    return json.jsonify({'success': False, 'message': msg})

def throw_error(request, msg, log=True):
    if log:
        embed = webhooks.build_caught_error(msg, request.remote_addr, request.path)
        webhooks.send_webhook(config['webhooks']['error'], embed)
    return json.jsonify({'success': False, 'message': msg})

# render_template override
def render_template(*args, **kwargs):
    return render_template_raw(*args,
        base_url=config['base_url'],
        favicon=config['favicon'],
        title=config['title'],
        cache_buster=config['cache_buster'],
        header_data=header_data,
        affiliate=session['affiliate'],
        **kwargs
    )

# SESSION AND AFFILIATE
@app.before_request
def before_request():
    if 'affiliate' not in session:
        session['affiliate'] = 'none'

@app.after_request
def after_request(response):
    blacklisted = ['/api/', '/a/', '/static/', '/favicon.ico']
    allowed = True
    for bl in blacklisted:
        if request.path.startswith(bl):
            allowed = False
    
    if allowed:
        database.add_tracking_event('VISIT', session['affiliate'], request)

    return response

@app.route('/a/<affiliate>', methods=['GET'])
def set_affiliate(affiliate):
    session['affiliate'] = affiliate
    return redirect('/')

# ROBOTS.TXT, SITEMAP and FAVICON
@app.route('/robots.txt', methods=['GET'])
def robots_txt():
    with open(config['robots.txt'], 'r') as f:
        data = f.read().replace('{{ base_url }}', config['base_url'])
    return Response(data, mimetype='text/plain')

@app.route('/sitemap.xml', methods=['GET'])
def sitemap_xml():
    with open(config['sitemap.xml'], 'r') as f:
        data = f.read().replace('{{ base_url }}', config['base_url'])
    return Response(data, mimetype='text/plain')

@app.route('/favicon.ico', methods=['GET'])
def favicon_ico():
    return send_file(config['favicon'])

# THE API
@app.route('/api/search/', methods=['GET'])
def api_search_empty():
    return json.dumps(lastfm.top())

@app.route('/api/search/<query>', methods=['GET'])
def api_search(query):
    try: return json.dumps(lastfm.search(query))
    except RuntimeError: return json.dumps([])

@app.route('/api/design/create', methods=['POST'])
def api_design_create():
    if not request.json: return throw_error(request, 'bad request')
    cover_data = request.json['cover_data']
    order_id, exists = database.new_design_id(cover_data)
    if not exists:
        design = printmachine.create_print(cover_data,
            cache=imgcache, album_size=config['design']['album_size'],
            design_size=config['design']['design_size'], design_gap=config['design']['design_gap'],
            album_layout=config['design']['album_layout'], background=tuple(config['design']['background']),
            border=tuple(config['design']['border']), border_size=config['design']['border_size'],
            logo_file=config['design']['logo_file'], logo_width=config['design']['logo_width'],
            logo_y_position=config['design']['logo_y_position'])
        database.upload_image(order_id, design, cover_data)
        del design

    database.add_tracking_event('PREVIEW', session['affiliate'], request)
    return json.dumps({ 'order_id': order_id })

# SHIRT SAVING - OUT OF ACTION FOR NOW
# @app.route('/api/order/save/<send_to>', methods=['POST'])
# def api_order_save(send_to):
#     order_id, exists = database.new_internal_id(request.json)
#     if not exists:
#         design = printmachine.create_print(request.json,
#             cache=imgcache, album_size=config['design']['album_size'],
#             design_size=config['design']['design_size'], design_gap=config['design']['design_gap'],
#             album_layout=config['design']['album_layout'], background=tuple(config['design']['background']),
#             border=tuple(config['design']['border']), border_size=config['design']['border_size'],
#             logo_file=config['design']['logo_file'], logo_width=config['design']['logo_width'],
#             logo_y_position=config['design']['logo_y_position'])
#         database.upload_image(order_id, design, request.json)
#         del design

#     url = config['base_url'] + '/load/%s' % order_id
#     database.add_tracking_event('SAVE', session['affiliate'], request, data='%s|%s|%s' % (send_to, order_id, session['affiliate']))

#     email = config['emails']['design_saved']

#     mailer.send_message(
#         send_to, email['name'], email['sender'],
#         email['subject'], open(email['body_file'], 'r').read(),
#         reply_to=email['reply_to'],
#         preview_url=config['base_url'] + '/api/order/mockup/' + order_id + '?width=500',
#         edit_url=config['base_url'] + '/load/' + order_id,
#         checkout_url=config['base_url'] + '/checkout/' + order_id
#     )

#     return json.dumps({ 'url': url, 'order': order_id, 'email': email })

@app.route('/api/design/<design_id>', methods=['GET'])
def api_design(design_id):
    width = request.args.get('width')
    design = database.get_image_data(design_id)
    if not design: return abort(404)

    img_io = io.BytesIO()
    mockup = printmachine.create_mockup(design, config['mockup']['blank'], config['mockup']['logo'])

    if width: mockup = printmachine.resize_image(mockup, width=int(width))

    mockup.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/api/design/<design_id>/raw', methods=['GET'])
def api_design_raw(design_id):
    width = request.args.get('width') # TODO: implement this
    image = database.get_image_data(design_id)
    if not image: return abort(404)

    response = make_response(image)
    response.headers.set('Content-Type', 'image/png')
    return response

@app.route('/api/order/price', methods=['GET'])
def api_order_price():
    item_name = request.args.get('item')
    promo_name = request.args.get('promo')

    if not item_name: return throw_error(request, 'please specify item')
    if item_name not in config['items']: return throw_error(request, 'no such item')
    if promo_name and (promo_name not in config['items'][item_name]['promos']):
        return throw_error(request, 'no such promo', log=False)
    
    promo = None
    item = config['items'][item_name]
    if promo_name: promo = item['promos'][promo_name]

    discount = 0
    base_price = item['price']
    if promo and promo['affects'] == 'price':
        discount = calculate_discount(promo, base_price)
    
    return json.jsonify({
        'success': True,
        'base_price': int(base_price),
        'final_price': int(base_price - discount),
        'discount': int(discount)
    })

@app.route('/api/order/shipping', methods=['GET'])
def api_order_shipping():
    country = request.args.get('country')
    promo_name = request.args.get('promo')
    item_name = request.args.get('item')

    if not country: return throw_error(request, 'please specify country')
    if not item_name: return throw_error(request, 'please specify item')
    if item_name not in config['items']: return throw_error(request, 'no such item')
    if promo_name and (promo_name not in config['items'][item_name]['promos']):
        return throw_error(request, 'no such promo', log=False)

    shipping_type = 'domestic' if country.upper() == 'US' else 'international'

    promo = None
    item = config['items'][item_name]
    if promo_name: promo = item['promos'][promo_name]

    discount = 0
    base_price = item['shipping'][shipping_type]
    if promo and promo['affects'] == 'shipping':
        discount = calculate_discount(promo, base_price)

    return json.jsonify({
        'success': True,
        'shipping_price': int(base_price - discount),
        'discount': discount
    })

@app.route('/api/order/create', methods=['POST'])
def api_order_create():
    if not request.json: return throw_error(request, 'bad request')
    if 'order_amount' not in request.json: throw_error(request, 'missing order_amount')

    try: order_amount = int(request.json['order_amount'])
    except ValueError: throw_error(request, 'order_amount must be an integer')
    if order_amount <= 0 or order_amount > 9999: return throw_error(request, 'invalid order amount')

    resp = paypal.create_order(order_amount)

    return json.jsonify({
        'success': True,
        'order_id': resp['id']
    })

@app.route('/api/order/finalize', methods=['POST'])
def api_order_process():
    if not request.json: return throw_error(request, 'bad request')

    try:
        paypal_id = request.json['order_id']
        item_name = request.json['item']
        promo_name = request.json['promo']
        details = request.json['details']
    except KeyError:
        return throw_error(request, 'missing request parameter(s)')

    if item_name not in config['items']: return throw_error(request, 'no such item')
    if promo_name and promo_name not in config['items'][item_name]['promos']:
        return throw_error(request, 'no such promo')

    promo = None
    item = config['items'][item_name]
    if promo_name: promo = item['promos'][promo_name]

    order_id = database.new_order_id()
    paypal.capture_payment(paypal_id) # payment is received HERE, throw CHECKOUT_ERROR for better logging (important)
    payment_details = paypal.get_order_details(paypal_id) # pull details from paypal api (kind of redundant but idc)
    total_price, total_shipping = paypal.PaymentBreakdown(payment_details)
    shipping = Paypal.ShippingInfo(payment_details)
    shipping_type = 'domestic' if shipping['country'].upper() == 'US' else 'international'
    contact = payment_details['payer']['email_address']

    expected_price = item['price']
    expected_shipping = item['shipping'][shipping_type]
    if promo and promo['affects'] == 'price':
        expected_price -= calculate_discount(promo, expected_price)
    if promo and promo['affects'] == 'shipping':
        expected_shipping -= calculate_discount(promo, expected_shipping)
    
    if int(total_price) < int(expected_price):
        return throw_checkout_error(request, 'total price too low (%s, %s)' % (total_price, promo_name), order_id, paypal_id, contact)
    if int(total_shipping) < int(expected_shipping):
        return throw_checkout_error(request, 'total shipping too low (%s, %s, %s)' % (total_shipping, shipping_type, promo_name), order_id, paypal_id, contact)

    if item_name == 'shirt':
        if 'design_id' not in details: return throw_checkout_error(request, 'invalid details for shirt', order_id, paypal_id, contact)
        if 'shirt_size' not in details: return throw_checkout_error(request, 'invalid details for shirt', order_id, paypal_id, contact)

        size = details['shirt_size'].upper()
        if size not in ['SMALL', 'MEDIUM', 'LARGE', 'EXTRALARGE']: return throw_checkout_error(request, 'invalid shirt size', order_id, paypal_id, contact)

        order_details = {
            'order_id': order_id,
            'paypal_id': payment_details['id'],
            'design_id': details['design_id'],
            'shirt_size': size,
            'order_status': 'PENDING',
            'first_name': payment_details['payer']['name']['given_name'],
            'last_name': payment_details['payer']['name']['surname'],
            'email': contact,
            'total_price': total_price,
            'total_shipping': total_shipping,
            'promo_code': promo_name,
            'addr_name': shipping['name'],
            'addr_line_1': shipping['address_1'],
            'addr_line_2': shipping['address_2'],
            'addr_city': shipping['city'],
            'addr_state': shipping['state'],
            'addr_zip_code': shipping['zip_code'],
            'addr_country': shipping['country'],
            'notes': ''
        }

        success, err = database.make_new_order(**order_details)
        if not success: return throw_checkout_error(request, err, order_id, paypal_id, contact)

        email = config['emails']['confirmation']
        mailer.send_message(
            order_details['email'], email['name'], email['sender'],
            email['subject'], open(email['body_file'], 'r').read(),
            reply_to=email['reply_to'],
            details_url=config['base_url'] + '/info/' + order_id,
            preview_url=config['base_url'] + '/api/design/' + details['design_id'] + '?width=900'
        )

        embed = webhooks.build_new_order(order_id, details['design_id'], order_details['first_name'], order_details['last_name'], config['base_url'])
        webhooks.send_webhook(config['webhooks']['order'], embed)

        if payment_details['status'] != 'COMPLETED': throw_checkout_error(request, 'paypal status not completed', order_id, paypal_id, contact)
        database.add_tracking_event('CHECKOUT', session['affiliate'], request)
        database.set_order_status(order_id, 'PAID')

        return json.jsonify({
            'success': success,
            'order_id': order_id
        })
    
    return throw_error('reached end of finalize with no result')

# USER PAGES
@app.route('/', methods=['GET'])
def index():
    return render_template('home.html')

@app.route('/tos', methods=['GET'])
def tos():
    return render_template('tos.html',
        contact_email=config['contact_email'],
        contact_address=config['contact_address']
    )

# SAVES SYSTEM DISABLED
# @app.route('/load/<order_id>', methods=['GET'])
# def load(order_id):
#     cover_data = database.get_image_details(order_id)
#     if not cover_data: return abort(404)

#     exists, affiliate = database.find_save_affiliate(order_id)
#     if exists: session['affiliate'] = affiliate

#     response = make_response(redirect('/?loaded=true'))
#     response.set_cookie('shirt-data', base64.b64encode(json.dumps(cover_data).encode('utf-8')))

#     database.add_tracking_event('LOAD', session['affiliate'], request, data=order_id)
#     return response

@app.route('/checkout/<design_id>', methods=['GET'])
def checkout(design_id):
    return render_template('checkout.html',
        design_id=design_id,
        item_details=json.dumps(config['items']['shirt']),
        paypal_client_id=config['paypal']['client_id']
    )

@app.route('/complete/<order_id>', methods=['GET'])
def complete(order_id):
    return render_template('complete.html', order_id=order_id)

@app.route('/info/<order_id>', methods=['GET'])
def info(order_id):
    exists, details = database.get_order_details(order_id)
    if not exists: return abort(404)
    else: return render_template('info.html', details=details)

if __name__ == '__main__':
    app.secret_key = b'Poop secret KEY!!'
    app.run(host='0.0.0.0', port=8104, debug=True)