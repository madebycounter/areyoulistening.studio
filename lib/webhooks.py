from discord_webhook import DiscordWebhook, DiscordEmbed
from threading import Thread

def send_webhook(url, embed):
    hook = DiscordWebhook(url=url)
    hook.add_embed(embed)
    thread = Thread(target=hook.execute)
    thread.start()

def build_new_order(order_id, design_id, first_name, last_name, base_url):
    image_url = base_url + '/api/design/' + design_id + '?width=400'
    title = '#%s' % order_id
    description = '%s %s' % (first_name, last_name)
    info_url = base_url + '/info/' + order_id
    color = 0x43b581

    embed = DiscordEmbed(title=title, description=description, color=color)
    embed.set_image(url=image_url)
    embed.set_url(url=info_url)
    return embed

def build_order_error(message, order_id, paypal_id, contact, base_url):
    title = 'Transaction Error'
    info_url = base_url + '/info/' + order_id
    description = 'Error: `%s`\nOrder ID: `%s`\nPaypal ID: `%s`\nContact: `%s`' % (message, order_id, paypal_id, contact)
    color = 0xfaa61a

    embed = DiscordEmbed(title=title, description=description, color=color)
    embed.set_url(url=info_url)
    return embed

def build_generic_error(title, message):
    color = 0xf04747
    embed = DiscordEmbed(title=title, description=message, color=color)
    return embed

def build_caught_error(message, ip, url):
    color = 0x71368a
    description = 'Message: `%s`\nIP: `%s`\nURL: `%s`' % (message, ip, url)
    embed = DiscordEmbed(title='Caught Exception', description=description, color=color)
    return embed