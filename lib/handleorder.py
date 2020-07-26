from .paypal import Paypal

def handle_order(details, internal_id, size, database=None, required_total=24):
    if not database: raise Exception('database parameter required')
    shipping = Paypal.ShippingInfo(details)

    order_details = {
        'paypal_id': details['id'],
        'internal_id': internal_id,
        'order_status': 'PAID' if details['status'] == 'COMPLETED' else 'ERROR',
        'first_name': details['payer']['name']['given_name'],
        'last_name': details['payer']['name']['surname'],
        'email': details['payer']['email_address'],
        'payer_id': details['payer']['payer_id'],
        'total': Paypal.OrderTotal(details),
        'shipping_name': shipping['name'],
        'address_1': shipping['address_1'],
        'address_2': shipping['address_2'],
        'state': shipping['state'],
        'city': shipping['city'],
        'zip_code': shipping['zip_code'],
        'shirt_size': size
    }

    if size not in ['small', 'medium', 'large', 'extralarge']: return False, 'invalid size', order_details['email']

    success, err = database.make_new_order(**order_details)
    if not success: return False, err, order_details['email']
    if not database.image_data_exists(internal_id): return False, 'image file not generated', order_details['email']
    if order_details['total'] < required_total: return False, 'insufficient funding', order_details['email']

    return True, order_details, order_details['email']