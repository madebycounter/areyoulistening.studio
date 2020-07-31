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
        conn = mysql.connector.connect(
            host=self.host,
            user=self.username,
            password=self.password,
            database=self.database
        )

        return conn, conn.cursor()
    
    def make_new_order(self, 
            paypal_id=None, internal_id=None, order_status=None, first_name=None,
            last_name=None, email=None, payer_id=None, total=None, shipping_name=None,
            address_1=None, address_2=None, state=None, city=None, zip_code=None,
            shirt_size=None, tracking_number=None, notes=None):

        try:
            conn, cur = self.generate_connection()

            query = 'SELECT COUNT(*) FROM `orders`'
            cur.execute(query)
            count = cur.fetchall()[0][0]
            friendly_name = '%s%s' % (str(count).zfill(4), first_name.lower())

            values = '(`paypal_id`, `internal_id`, `friendly_name`, `order_status`, `create_time`, `first_name`, `last_name`, `email`, `payer_id`, `total`, `shipping_name`, `address_1`, `address_2`, `state`, `city`, `zip_code`, `shirt_size`, `tracking_number`, `notes`)'
            query = 'INSERT INTO `orders` ' + values + ' VALUES (' + ('%s,' * 19)[:-1] + ')'
            cur.execute(query, \
                    (paypal_id, internal_id, friendly_name, order_status, int(time.time()), first_name, \
                    last_name, email, payer_id, int(total * 100), shipping_name, address_1, \
                    address_2, state, city, zip_code, shirt_size, tracking_number, notes))
            conn.commit()
        except Error as error:
            return False, 'database error'
        finally:
            conn.close()
            cur.close()
        return True, 'success'
    
    def new_internal_id(self, length=16):
        conn, cur = self.generate_connection()

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
            conn, cur = self.generate_connection()
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
        conn, cur = self.generate_connection()
        cur.execute('''SELECT image FROM `images` WHERE internal_id=%s''', (internal_id,))
        results = cur.fetchall()
        conn.close()
        cur.close()

        if not len(results): return False
        # elif not len(results[0][0]): return False
        else: return results[0][0]
    
    def delete_image_data(self, internal_id):
        conn, cur = self.generate_connection()
        cur.execute('''
            UPDATE `images` SET image=%s, has_blob=%s WHERE internal_id=%s
        ''', (None, False, internal_id))
        conn.commit()
        conn.close()
        cur.close()
    
    def image_data_exists(self, internal_id):
        conn, cur = self.generate_connection()
        cur.execute('''SELECT count(*) FROM `images` WHERE internal_id=%s AND has_blob=1''', (internal_id,))
        results = cur.fetchall()
        conn.close()
        cur.close()

        return bool(results[0][0])
    
    def get_order_details(self, internal_id):
        conn, cur = self.generate_connection()
        cur.execute('''SELECT * FROM `orders` WHERE internal_id=%s''', (internal_id,))
        results = cur.fetchall()
        conn.close()
        cur.close()

        if len(results) == 0:
            return False, {}
        else:
            return True, {
                'paypal_id': results[0][0],
                'internal_id': results[0][1],
                'friendly_name': results[0][2], # aaa
                'order_status': results[0][3],
                'create_time': results[0][4],
                'first_name': results[0][5],
                'last_name': results[0][6],
                'email': results[0][7],
                'payer_id': results[0][8],
                'total': results[0][9],
                'shipping_name': results[0][10],
                'address_1': results[0][11],
                'address_2': results[0][12],
                'state': results[0][13],
                'city': results[0][14],
                'zip_code': results[0][15],
                'shirt_size': results[0][16],
                'tracking_number': results[0][17],
                'notes': results[0][18]
            }

    def set_order_status(self, internal_id, status):
        if status not in ['PAID', 'ORDERED', 'SHIPPED', 'ERROR']: raise Exception('invalid status')
        conn, cur = self.generate_connection()
        cur.execute('''UPDATE `orders` SET order_status=%s WHERE internal_id=%s''', (status, internal_id,))
        conn.commit()
        conn.close()
        cur.close()

    def add_tracking_event(self, event, affiliate, request, data=None):
        if event not in ['VISIT', 'PREVIEW', 'CHECKOUT']: raise Exception('invalid event')
        conn, cur = self.generate_connection()

        version = request.user_agent.version and int(request.user_agent.version.split('.')[0])
        browser = request.user_agent.browser + ' ' + str(version)
        platform = request.user_agent.platform
        address = request.remote_addr
        url = request.path[:128]
        user_agent = request.user_agent.string

        sql = '''INSERT INTO `tracking` (`id`, `event`, `time`, `address`, `affiliate`, `url`, `browser`, `platform`, `user_agent`, `data`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'''
        cur.execute(sql, (None, event, int(time.time()), address, affiliate, url, browser, platform, user_agent, data))
        conn.commit()
        conn.close()
        cur.close()