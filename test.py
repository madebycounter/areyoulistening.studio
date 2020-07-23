from lib import config, LastFM, ImageCache, Paypal, Database, Mailer, printmachine

lastfm = LastFM(config['lastfm']['api_key'], cache=config['lastfm']['cache'])
imgcache = ImageCache(data=config['covers']['data_file'], dump=config['covers']['dump_dir'])
paypal = Paypal(config['paypal']['client_id'], config['paypal']['client_secret'], api_url=config['paypal']['api_url'])
mailer = Mailer(config['mailgun']['api_key'], config['mailgun']['api_domain'], api_url=config['mailgun']['api_url'])
database = Database(host=config['database']['host'], username=config['database']['username'],
                    password=config['database']['password'], database=config['database']['database'])



data = {
    'first_name': 'William',
    'ship_to': '1908 crestmont drive',
    'size': 'Medium',
    'internal_id': '51bd67ec',
    'base_url': 'http://75.49.248.98:8104/'
}

r = mailer.send_message(
    'wg4568@gmail.com',
    config['emails']['confirmation']['name'],
    config['emails']['confirmation']['sender'],
    config['emails']['confirmation']['subject'],
    open(config['emails']['confirmation']['body_file'], 'r').read(),
    **data
)

print(r)
print(r.text)

# database.delete_image_data('3eada9c9')

# print(database.image_data_exists('3eada9c9'))

# img_data = [[{"image":"https://lastfm.freetls.fastly.net/i/u/300x300/f669cf23955770f9100ab7c0a65b5853.png","title":"When We Were Friends","artist":"The Backseat Lovers"},{"image":"https://lastfm.freetls.fastly.net/i/u/300x300/23c5e3b982d441d690315efa25844ddd.png","title":"Help!","artist":"The Beatles"},{"image":"https://lastfm.freetls.fastly.net/i/u/300x300/2eda9f816512d29556f8a9df10148228.png","title":"A","artist":"The Slaps"}],[{"image":"https://lastfm.freetls.fastly.net/i/u/300x300/5da585a71460c0448c4e8ea5071bf9ec.png","title":"Nothing Happens","artist":"Wallows"},{"image":"https://lastfm.freetls.fastly.net/i/u/300x300/14c30e757fdd4dcf8f8b0884506a7303.png","title":"F O R T R E S S","artist":"Miniature Tigers"},{"image":"https://lastfm.freetls.fastly.net/i/u/300x300/35ade73a0ba2df53e2eac1cee575d229.png","title":"R.I.P.","artist":"Naked Giants"}],[{"image":"https://lastfm.freetls.fastly.net/i/u/300x300/13d604e0980e3c3aa9a06ab413a89bdd.png","title":"Being so Normal","artist":"Peach Pit"},{"image":"https://lastfm.freetls.fastly.net/i/u/300x300/c5dd76a28e2d44fac40d23ce64c352dc.png","title":"Grown Up Wrong","artist":"Native America"},{"image":"https://lastfm.freetls.fastly.net/i/u/300x300/99dad37e7e2d444ac415e9c30ebb2b9c.png","title":"Careful Kid","artist":"Yabadum"}]]
# order_id = database.new_internal_id()

# design = PrintMachine(img_data,
#     cache=imgcache, album_size=config['design']['album_size'],
#     design_size=config['design']['design_size'], design_gap=config['design']['design_gap'],
#     album_layout=config['design']['album_layout'], background=tuple(config['design']['background']),
#     border=tuple(config['design']['border']), border_size=config['design']['border_size']
# )

# database.upload_image(order_id, design, img_data)
