from discord_webhook import DiscordWebhook, DiscordEmbed
from threading import Thread

def send_webhook(url, embed):
    hook = DiscordWebhook(url=url)
    hook.add_embed(embed)
    thread = Thread(target=hook.execute)
    thread.start()

def build_new_order(order_id, first_name, last_name, base_url):
    image_url = base_url + '/api/order/mockup/' + order_id + '?width=400'
    title = '#%s' % order_id
    description = '%s %s' % (first_name, last_name)

    embed = DiscordEmbed(title=title, description=description)
    embed.set_image(url=image_url)
    return embed