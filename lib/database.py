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

        self.floated_design_ids = []
        self.floated_order_ids = []

    def generate_connection(self):
        conn = mysql.connector.connect(
            host=self.host,
            user=self.username,
            password=self.password,
            database=self.database,
            charset='utf8'
        )

        return conn, conn.cursor()
    
    def make_new_order(self, 
            order_id=None, paypal_id=None, design_id=None, shirt_size=None, order_status=None,
            first_name=None, last_name=None, email=None, total_price=None, total_shipping=None, promo_code=None,
            addr_name=None, addr_line_1=None, addr_line_2=None, addr_city=None, addr_state=None,
            addr_zip_code=None, addr_country=None, notes=None):

        try:
            conn, cur = self.generate_connection()

            query = 'SELECT COUNT(*) FROM `orders`'
            cur.execute(query)
            count = cur.fetchall()[0][0]
            friendly_name = '%s%s' % (str(count).zfill(4), first_name.lower())

            values = '(`order_id`, `paypal_id`, `design_id`, `shirt_size`, `friendly_name`, `order_status`, `create_time`, `first_name`, `last_name`, `email`, `total_price`, `total_shipping`, `promo_code`, `addr_name`, `addr_line_1`, `addr_line_2`, `addr_city`, `addr_state`, `addr_zip_code`, `addr_country`, `notes`)'
            query = 'INSERT INTO `orders` ' + values + ' VALUES (' + ('%s,' * 21)[:-1] + ')'
            cur.execute(query, \
                    (order_id, paypal_id, design_id, shirt_size, friendly_name, order_status, int(time.time()), \
                     first_name, last_name, email, total_price, total_shipping, promo_code, addr_name, \
                     addr_line_1, addr_line_2, addr_city, addr_state, addr_zip_code, addr_country, notes))
            conn.commit()

            if order_id in self.floated_order_ids:
                self.floated_order_ids.remove(order_id)
        except Error as error:
            return False, 'database error'
        finally:
            conn.close()
            cur.close()
        return True, 'success'
    
    def new_design_id(self, albums, length=16):
        conn, cur = self.generate_connection()

        album_info = []
        for x in range(len(albums)):
            for y in range(len(albums[0])):
                album_info.append('%s|%s|%s' % (albums[x][y]['title'], albums[x][y]['artist'], albums[x][y]['image']))

        album_concat = ''.join(album_info)
        cur.execute('''SELECT design_id FROM `images` WHERE concat(album_00, album_01, album_02, album_10, album_11, album_12, album_20, album_21, album_22) = %s''', (album_concat,))
        results = cur.fetchall()
        if len(results): return results[0][0], True

        results = [(1,)]
        design_id = None
        while results[0][0] or design_id in self.floated_design_ids:
            design_id = random_string(length)
            cur.execute('''SELECT count(*) FROM `images` WHERE design_id=%s''', (design_id,))
            results = cur.fetchall()

        self.floated_design_ids.append(design_id)
        return design_id, False
 
    def new_order_id(self, length=12):
        conn, cur = self.generate_connection()

        results = [(1,)]
        order_id = None
        while results[0][0] or order_id in self.floated_order_ids:
            order_id = random_string(length).upper()
            cur.execute('''SELECT count(*) FROM `orders` WHERE order_id=%s''', (order_id,))
            results = cur.fetchall()

        self.floated_order_ids.append(order_id)
        return order_id

    def upload_image(self, design_id, image, albums):
        album_info = []
        for x in range(len(albums)):
            for y in range(len(albums[0])):
                album_info.append('%s|%s|%s' % (albums[x][y]['title'], albums[x][y]['artist'], albums[x][y]['image']))

        try:
            conn, cur = self.generate_connection()
            cur.execute('''
                INSERT INTO images VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (design_id, image_to_byte_array(image), True) + tuple(album_info))
            conn.commit()

            if design_id in self.floated_design_ids:
                self.floated_design_ids.remove(design_id)
        except Error as error:
            return False, 'an unknown database error occured'
        finally:
            conn.close()
            cur.close()
        return True, 'success'
    
    def get_image_details(self, design_id):
        conn, cur = self.generate_connection()
        cur.execute('''SELECT album_00, album_01, album_02, album_10, album_11, album_12, album_20, album_21, album_22 FROM `images` WHERE design_id=%s''', (design_id,))
        results = cur.fetchall()
        conn.close()
        cur.close()

        if not len(results): return False
        else:
            cover_data = []
            for x in range(3):
                cover_data.append([])
                for y in range(3):
                    idx = (x * 3) + y
                    title, artist, image = str(results[0][idx]).split('|')
                    cover_data[x].append({
                        'artist': artist,
                        'image': image,
                        'title': title
                    })
        
        return cover_data

    def get_image_data(self, design_id):
        conn, cur = self.generate_connection()
        cur.execute('''SELECT image FROM `images` WHERE design_id=%s''', (design_id,))
        results = cur.fetchall()
        conn.close()
        cur.close()

        if not len(results): return False
        # elif not len(results[0][0]): return False
        else: return results[0][0]
    
    def delete_image_data(self, design_id):
        conn, cur = self.generate_connection()
        cur.execute('''
            UPDATE `images` SET image=%s, has_blob=%s WHERE design_id=%s
        ''', (None, False, design_id))
        conn.commit()
        conn.close()
        cur.close()
    
    def image_data_exists(self, design_id):
        conn, cur = self.generate_connection()
        cur.execute('''SELECT count(*) FROM `images` WHERE design_id=%s AND has_blob=1''', (design_id,))
        results = cur.fetchall()
        conn.close()
        cur.close()

        return bool(results[0][0])
    
    def find_save_affiliate(self, design_id):
        conn, cur = self.generate_connection()
        query = '''
            SELECT
                SUBSTRING_INDEX(
                    SUBSTRING_INDEX(data, '|', 2),
                    '|', -1) AS design_id,
                SUBSTRING_INDEX(data, '|', -1) AS affiliate
            FROM tracking
            WHERE event="SAVE"
            HAVING design_id=%s
        '''
        cur.execute(query, (design_id,))
        results = cur.fetchall()

        if not len(results):
            return False, ''
        else:
            return True, results[0][1]

    def get_order_details(self, order_id):
        conn, cur = self.generate_connection()
        cur.execute('''SELECT * FROM `orders` WHERE order_id=%s''', (order_id,))
        results = cur.fetchall()
        conn.close()
        cur.close()

        if len(results) == 0:
            return False, {}
        else:
            return True, {
                'order_id': results[0][0],
                'paypal_id': results[0][1],
                'design_id': results[0][2],
                'shirt_size': results[0][3],
                'friendly_name': results[0][4],
                'order_status': results[0][5],
                'create_time': results[0][6],
                'first_name': results[0][7],
                'last_name': results[0][8],
                'email': results[0][9],
                'total_price': results[0][10],
                'total_shipping': results[0][11],
                'promo_code': results[0][12],
                'addr_name': results[0][13],
                'addr_line_1': results[0][14],
                'addr_line_2': results[0][15],
                'addr_city': results[0][16],
                'addr_state': results[0][17],
                'addr_zip_code': results[0][18],
                'addr_country': results[0][19],
                'notes': results[0][20]
            }

    def set_order_status(self, order_id, status):
        if status not in ['PENDING', 'PAID', 'ORDERED', 'SHIPPED', 'ERROR']: raise Exception('invalid status')
        conn, cur = self.generate_connection()
        cur.execute('''UPDATE `orders` SET order_status=%s WHERE order_id=%s''', (status, order_id,))
        conn.commit()
        conn.close()
        cur.close()

    def add_tracking_event(self, event, affiliate, request, data=None):
        if event not in ['VISIT', 'PREVIEW', 'CHECKOUT', 'ERROR', 'SAVE', 'LOAD']: raise Exception('invalid event')
        conn, cur = self.generate_connection()

        version = request.user_agent.version and int(request.user_agent.version.split('.')[0])
        browser = request.user_agent.browser + ' ' + str(version)
        platform = request.user_agent.platform
        address = request.remote_addr
        url = request.path[:128]
        user_agent = request.user_agent.string[:256]

        sql = '''INSERT INTO `tracking` (`id`, `event`, `time`, `address`, `affiliate`, `url`, `browser`, `platform`, `user_agent`, `data`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'''
        cur.execute(sql, (None, event, int(time.time()), address, affiliate, url, browser, platform, user_agent, data))
        conn.commit()
        conn.close()
        cur.close()