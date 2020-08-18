from .paypal import Paypal

def handle_order(details, order_id, design_id, shipping, payments, size, database=None):
    if not database: raise Exception('database parameter required')

    order_details = {
        'order_id': order_id,
        'paypal_id': details['id'],
        'design_id': design_id,
        'shirt_size': size.upper(),
        'order_status': 'PAID' if details['status'] == 'COMPLETED' else 'ERROR',
        'first_name': details['payer']['name']['given_name'],
        'last_name': details['payer']['name']['surname'],
        'email': details['payer']['email_address'],
        'total_price': payments[0],
        'total_shipping': payments[1],
        'shipping_name': shipping['name'],
        'address_1': shipping['address_1'],
        'address_2': shipping['address_2'],
        'state': shipping['state'],
        'city': shipping['city'],
        'zip_code': shipping['zip_code'],
        'notes': ''
    }

    if size.upper() not in ['SMALL', 'MEDIUM', 'LARGE', 'EXTRALARGE']: return False, 'invalid size', order_details['email']

    success, err = database.make_new_order(**order_details)
    if not success: return False, err, order_details['email']
    if not database.image_data_exists(internal_id): return False, 'image file not generated', order_details['email']

    return True, order_details, order_details['email']