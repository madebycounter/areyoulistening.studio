import requests
import time
import json

def regenerate_token(func):
    def wrapped(self, *args, **kwargs):
        if self.need_new_token():
            self.get_access_token()
        return func(self, *args, **kwargs)
    return wrapped

class Paypal():
    def __init__(self, client_id, client_secret, api_url='https://api.sandbox.paypal.com', verbose=True):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = api_url
        self.session = requests.Session()
        self.verbose = verbose

        self.access_token = None
        self.access_token_created = None
        self.access_token_life = None

    def _log(self, *args, **kwargs):
        if self.verbose:
            print('[Paypal]', *args, **kwargs)

    def need_new_token(self):
        if not self.access_token: return True
        return time.time() - self.access_token_created > self.access_token_life

    def get_access_token(self):
        resp = self.session.post(self.api_url + '/v1/oauth2/token', auth=(self.client_id, self.client_secret), data={'grant_type': 'client_credentials'})
        self.access_token = resp.json()['access_token']
        self.access_token_life = resp.json()['expires_in']
        self.access_token_created = time.time()
        self.session.headers.update({
            'Authorization': 'Bearer %s' % self.access_token,
            'Content-Type': 'application/json'
        })
        self._log('Updated access token, expires in %s' % resp.json()['expires_in'])

    @regenerate_token
    def create_order(self, amount, currency='USD'):
        resp = self.session.post(self.api_url + '/v2/checkout/orders', data=json.dumps({
            'intent': 'CAPTURE',
            'purchase_units': [{
                'amount': {
                    'currency_code': currency,
                    'value': round(amount / 100, 2)
                }
            }]
        }))

        if 'id' in resp.json():
            self._log('Created order \'%s\', total: %s %s' % (resp.json()['id'], round(amount / 100, 2), currency))

        return resp.json()

    @regenerate_token
    def get_order_details(self, order_id):
        resp = self.session.get(self.api_url + '/v2/checkout/orders/' + order_id)
        self._log('Retrieved order details for %s' % order_id)
        return resp.json()

    @regenerate_token
    def get_capture_details(self, cap_id):
        resp = self.session.get(self.api_url + '/v2/payments/captures/' + cap_id)
        return resp.json()

    @regenerate_token
    def capture_payment(self, order_id):
        resp = self.session.post(self.api_url + '/v2/checkout/orders/' + order_id + '/capture')
        self._log('Captured payments for %s' % order_id)
        return resp.json()

    @staticmethod
    def PaymentBreakdown(details, currency='USD'):
        total_price = 0
        total_shipping = 0
        for purchase_unit in details['purchase_units']:
            breakdown = purchase_unit['amount']['breakdown']
            if breakdown['item_total']['currency_code'].upper() == currency:
                total_price += int(100 * float(breakdown['item_total']['value']))
            if breakdown['shipping']['currency_code'].upper() == currency:
                total_shipping += int(100 * float(breakdown['shipping']['value']))

        return total_price, total_shipping

    @staticmethod
    def ShippingInfo(details):
        info = details['purchase_units'][0]['shipping']
        return {
            'name': info['name']['full_name'],
            'address_1': info['address']['address_line_1'],
            'address_2': '' if 'address_line_2' not in info['address'] else info['address']['address_line_2'],
            'city': info['address']['admin_area_2'],
            'state': info['address']['admin_area_1'],
            'zip_code': info['address']['postal_code'],
            'country': info['address']['country_code']
        }