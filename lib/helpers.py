import random

def random_string(length):
    return ('%0x' % random.getrandbits(length * 8))[:length]

def calculate_discount(promo, price):
    deduction = 0
    if promo['type'] == 'percent': deduction = price * promo['amount'] / 100
    elif promo['type'] == 'deduction': deduction = promo['amount']

    if deduction > price: deduction = price
    return int(deduction)