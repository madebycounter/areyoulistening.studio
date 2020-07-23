import random

def random_string(length):
    return ('%0x' % random.getrandbits(length * 8))[:length]