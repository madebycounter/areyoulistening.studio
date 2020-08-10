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
    info_url = base_url + '/info/' + order_id
    color = 0x001d85

    embed = DiscordEmbed(title=title, description=description, color=color)
    embed.set_image(url=image_url)
    embed.set_url(url=info_url)
    return embed

def build_error(order_id, message, contact, base_url):
    title = 'Transaction Error'
    info_url = base_url + '/info/' + order_id
    description = 'Error: `%s`\nOrder ID: `%s`\nContact: `%s`' % (message, order_id, contact)
    color = 0x850000

    embed = DiscordEmbed(title=title, description=description, color=color)
    embed.set_url(url=info_url)
    return embed

def build_generic_error(title, message):
    color = 0x850000
    embed = DiscordEmbed(title=title, description=message, color=color)
    return embed