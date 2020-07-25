from lib import LastFM, ImageCache, Paypal, Database, Mailer, printmachine, webhooks, handle_order
from flask import Flask, render_template, request, send_file, make_response, abort
import json
import time
import random
import io
import os

with open(os.environ['AYL_CONFIG'], 'r') as f:
    config = json.load(f)

lastfm = LastFM(config['lastfm']['api_key'], cache=config['lastfm']['cache'])
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
    return render_template('error.html', error_code=500), 500

# THE API
@app.route('/api/search/<query>', methods=['GET'])
def api_search(query):
    return json.dumps(lastfm.search(query))

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
        border=tuple(config['design']['border']), border_size=config['design']['border_size'])
    database.upload_image(order_id, design, request.json)
    del design

    return json.dumps({ 'order': order_id })

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

    # paypal_id
    # internal_id
    # order_status
    # first_name
    # last_name
    # email
    # payer_id
    # total
    # shipping_name
    # address_1
    # address_2
    # state
    # city
    # zip_code
    # shirt_size

    if success:
        email = config['emails']['confirmation']
        mailer.send_message(
            data['email'], email['name'], email['sender'],
            email['subject'], open(email['body_file'], 'r').read(),
            base_url=config['base_url'], **data
        )

        embed = webhooks.build_new_order(order_id, data['first_name'], data['last_name'], config['base_url'])
        webhooks.send_webhook(config['webhook'], embed)

    if not success:
        embed = webhooks.build_error(order_id, str(data), contact, config['base_url'])
        webhooks.send_webhook(config['webhook'], embed)

    return json.dumps({
        'success': success,
        'message': data
    })


# USER PAGES
@app.route('/', methods=['GET'])
def index():
    return render_template('home.html')

@app.route('/checkout/<order_id>', methods=['GET'])
def checkout(order_id):
    return render_template('checkout.html', order_id=order_id)

@app.route('/complete/<order_id>', methods=['GET'])
def complete(order_id):
    return render_template('complete.html', order_id=order_id)

@app.route('/info/<order_id>', methods=['GET'])
def info(order_id):
    exists, details = database.get_order_details(order_id)
    if not exists: abort(404)
    else: return render_template('info.html', details=details)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8104, debug=True)