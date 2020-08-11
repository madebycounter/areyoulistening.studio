from lib import LastFM, ImageCache, Paypal, Database, Mailer, printmachine, webhooks, handle_order
from flask import Flask, render_template as render_template_raw, request, send_file, make_response, abort, Response, session, redirect
import json
import time
import random
import io
import os
import re
import base64

with open(os.environ['AYL_CONFIG'], 'r') as f:
    config = json.load(f)

with open(config['header_data'], 'r') as f:
    header_data = f.read()

if config['cache_buster'] == 'RANDOM':
    config['cache_buster'] = random.randint(10000, 99999)

lastfm = LastFM(config['lastfm']['api_key'], cache=config['lastfm']['cache'], use_api_for_top=config['lastfm']['use_api_for_top'],
                top_albums_file=config['lastfm']['top_albums_file'], cache_age=config['lastfm']['cache_age'])
imgcache = ImageCache(data=config['covers']['data_file'], dump=config['covers']['dump_dir'])
paypal = Paypal(config['paypal']['client_id'], config['paypal']['client_secret'], api_url=config['paypal']['api_url'])
mailer = Mailer(config['mailgun']['api_key'], config['mailgun']['api_domain'], api_url=config['mailgun']['api_url'])
database = Database(host=config['database']['host'], username=config['database']['username'],
                    password=config['database']['password'], database=config['database']['database'])

app = Flask(__name__, template_folder=config['templates_folder'])

# ERRORS
@app.errorhandler(404)
def error_404(e):
    return render_template('error.html', error_code=404), 404

@app.errorhandler(500)
def error_500(e):
    database.add_tracking_event('ERROR', 'none', request, data='generic error')
    return render_template('error.html', error_code=500), 500

@app.errorhandler(Exception)
def handle_exception(e):
    embed = webhooks.build_generic_error('Server Error', 'Error: `%s`\nIP: `%s`\nURL: `%s`' % (request.remote_addr, str(e), request.path))
    webhooks.send_webhook(config['webhooks']['error'], embed)
    database.add_tracking_event('ERROR', 'none', request, data=str(e))
    return render_template('error.html', error_code=500), 500

def render_template(*args, **kwargs):
    return render_template_raw(*args,
        base_url=config['base_url'],
        favicon=config['favicon'],
        title=config['title'],
        cache_buster=config['cache_buster'],
        header_data=header_data,
        **kwargs
    )

# SESSION AND AFFILIATE
@app.after_request
def after_request(response):
    if 'affiliate' not in session:
        session['affiliate'] = 'none'

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

# ROBOTS.TXT and SITEMAP
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

@app.route('/api/top', methods=['GET'])
def api_top():
    return json.dumps(lastfm.top())

@app.route('/api/order/create', methods=['POST'])
def api_order_create():
    order_id = database.new_internal_id()
    design = printmachine.create_print(request.json,
        cache=imgcache, album_size=config['design']['album_size'],
        design_size=config['design']['design_size'], design_gap=config['design']['design_gap'],
        album_layout=config['design']['album_layout'], background=tuple(config['design']['background']),
        border=tuple(config['design']['border']), border_size=config['design']['border_size'],
        logo_file=config['design']['logo_file'], logo_width=config['design']['logo_width'],
        logo_y_position=config['design']['logo_y_position'])
    database.upload_image(order_id, design, request.json)
    del design

    database.add_tracking_event('PREVIEW', session['affiliate'], request)
    return json.dumps({ 'order': order_id })

@app.route('/api/order/save', methods=['POST'])
def api_order_save():
    order_id = database.new_internal_id()
    design = printmachine.create_print(request.json,
        cache=imgcache, album_size=config['design']['album_size'],
        design_size=config['design']['design_size'], design_gap=config['design']['design_gap'],
        album_layout=config['design']['album_layout'], background=tuple(config['design']['background']),
        border=tuple(config['design']['border']), border_size=config['design']['border_size'],
        logo_file=config['design']['logo_file'], logo_width=config['design']['logo_width'],
        logo_y_position=config['design']['logo_y_position'])
    database.upload_image(order_id, design, request.json)
    del design

    url = config['base_url'] + '/load/%s' % order_id
    database.add_tracking_event('SAVE', session['affiliate'], request)

    # do email stuff

    return json.dumps({ 'url': url, 'order': order_id })

@app.route('/api/order/mockup/<order_id>', methods=['GET'])
def api_mockup(order_id):
    width = request.args.get('width')
    design = database.get_image_data(order_id)
    if not design: return abort(404)

    img_io = io.BytesIO()
    mockup = printmachine.create_mockup(design, config['mockup']['blank'], config['mockup']['logo'])

    if width: mockup = printmachine.resize_image(mockup, width=int(width))

    mockup.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/api/order/design/<order_id>', methods=['GET'])
def api_design(order_id):
    image = database.get_image_data(order_id)
    if not image: return abort(404)

    response = make_response(image)
    response.headers.set('Content-Type', 'image/png')
    return response

@app.route('/api/order/process/<paypal_id>/<order_id>/<size>', methods=['GET'])
def api_order_process(paypal_id, order_id, size):
    details = paypal.get_order_details(paypal_id)
    total = Paypal.OrderTotal(details)
    success, data, contact = handle_order(details, order_id, size, database=database)

    if success:
        email = config['emails']['confirmation']
        mailer.send_message(
            data['email'], email['name'], email['sender'],
            email['subject'], open(email['body_file'], 'r').read(),
            base_url=config['base_url'], **data
        )

        embed = webhooks.build_new_order(order_id, data['first_name'], data['last_name'], config['base_url'])
        webhooks.send_webhook(config['webhooks']['order'], embed)

        database.add_tracking_event('CHECKOUT', session['affiliate'], request)

    if not success:
        embed = webhooks.build_error(order_id, str(data), contact, config['base_url'])
        webhooks.send_webhook(config['webhooks']['error'], embed)
        database.set_order_status(order_id, 'ERROR')

    return json.dumps({
        'success': success,
        'message': data
    })

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

@app.route('/load/<order_id>', methods=['GET'])
def load(order_id):
    cover_data = database.get_image_details(order_id)
    if not cover_data: abort(404)

    print(json.dumps(cover_data))

    response = make_response(redirect('/?loaded=%s' % order_id))
    response.set_cookie('shirt-data', json.dumps(cover_data))
    return response

@app.route('/checkout/<order_id>', methods=['GET'])
def checkout(order_id):
    return render_template('checkout.html',
        order_id=order_id,
        paypal_client_id=config['paypal']['client_id']
    )

@app.route('/complete/<order_id>', methods=['GET'])
def complete(order_id):
    return render_template('complete.html', order_id=order_id)

@app.route('/info/<order_id>', methods=['GET'])
def info(order_id):
    exists, details = database.get_order_details(order_id)
    if not exists: abort(404)
    else: return render_template('info.html', details=details)

if __name__ == '__main__':
    app.secret_key = b'Poop secret KEY!'
    app.run(host='0.0.0.0', port=8104, debug=True)