from .helpers import random_string
from mysql.connector import Error
import mysql.connector
import time
import io

def image_to_byte_array(image):
    byte_array = io.BytesIO()
    image.save(byte_array, format='png')
    return byte_array.getvalue()

class Database:
    def __init__(self, host=None, username=None, password=None, database=None):
        self.host = host
        self.username = username
        self.password = password
        self.database = database

        self.floated_ids = []

    def generate_connection(self):
        return mysql.connector.connect(
            host=self.host,
            user=self.username,
            password=self.password,
            database=self.database
        )
    
    def make_new_order(self, 
            paypal_id=None, internal_id=None, order_status=None, first_name=None,
            last_name=None, email=None, payer_id=None, total=None, shipping_name=None,
            address_1=None, address_2=None, state=None, city=None, zip_code=None,
            shirt_size=None):

        try:
            conn = self.generate_connection()
            cur = conn.cursor()
            values = '(`paypal_id`, `internal_id`, `order_status`, `create_time`, `first_name`, `last_name`, `email`, `payer_id`, `total`, `shipping_name`, `address_1`, `address_2`, `state`, `city`, `zip_code`, `shirt_size`)'
            query = 'INSERT INTO `orders` ' + values + ' VALUES (' + ('%s,' * 16)[:-1] + ')'
            cur.execute(query, \
                    (paypal_id, internal_id, order_status, int(time.time()), first_name, \
                    last_name, email, payer_id, int(total * 100), shipping_name, \
                    address_1, address_2, state, city, zip_code, shirt_size))
            conn.commit()
        except Error as error:
            return False, 'database error'
        finally:
            conn.close()
            cur.close()
        return True, 'success'
    
    def new_internal_id(self, length=8):
        conn = self.generate_connection()
        cur = conn.cursor()

        results = [(1,)]
        internal_id = None
        while results[0][0] or internal_id in self.floated_ids:
            internal_id = random_string(length)
            cur.execute('''SELECT count(*) FROM `images` WHERE internal_id=%s''', (internal_id,))
            results = cur.fetchall()

        self.floated_ids.append(internal_id)
        return internal_id
 
    def upload_image(self, internal_id, image, albums):
        album_info = []
        for x in range(len(albums)):
            for y in range(len(albums[0])):
                album_info.append('%s|%s|%s' % (albums[x][y]['title'], albums[x][y]['artist'], albums[x][y]['image']))

        try:
            conn = self.generate_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO images VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (internal_id, image_to_byte_array(image), True) + tuple(album_info))
            conn.commit()

            if internal_id in self.floated_ids:
                self.floated_ids.remove(internal_id)
        except Error as error:
            return False, 'an unknown database error occured'
        finally:
            conn.close()
            cur.close()
        return True, 'success'
    
    def get_image_data(self, internal_id):
        conn = self.generate_connection()
        cur = conn.cursor()
        cur.execute('''SELECT image FROM `images` WHERE internal_id=%s''', (internal_id,))
        results = cur.fetchall()
        conn.close()
        cur.close()

        if not len(results): return False
        # elif not len(results[0][0]): return False
        else: return results[0][0]
    
    def delete_image_data(self, internal_id):
        conn = self.generate_connection()
        cur = conn.cursor()
        cur.execute('''
            UPDATE `images` SET image=%s, has_blob=%s WHERE internal_id=%s
        ''', (None, False, internal_id))
        conn.commit()
        conn.close()
        cur.close()
    
    def image_data_exists(self, internal_id):
        conn = self.generate_connection()
        cur = conn.cursor()
        cur.execute('''SELECT count(*) FROM `images` WHERE internal_id=%s AND has_blob=1''', (internal_id,))
        results = cur.fetchall()
        conn.close()
        cur.close()

        return bool(results[0][0])

# mydb = Database(
#     host="areyoulistening.studio",
#     username="ayl-prod",
#     password="bYAPF7M4q86m4Zfr5NUMmjpZBT4EnwUt",
#     database="areyoulistening"
# )

# mydb.delete_image_data('68ac1e62')

# s, e =mydb.make_new_order(
#     paypal_id=random_string(8), internal_id='internal_id', order_status='order_status', first_name='first_name',
#     last_name='last_name', email='email', payer_id='payer_id', total=27.50
# )

# print(s, e)