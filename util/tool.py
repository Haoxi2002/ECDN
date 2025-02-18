import random
import string

import xxhash


def cdn_hash(content: str):
    hash_max = 2147483647
    return xxhash.xxh64(content).intdigest() % hash_max


class Hostname_Generator:
    def __init__(self):
        self.l = []

    def generate(self):
        new_hostname = f"bkj-{''.join(random.choices(string.hexdigits, k=8)).upper()}"
        while new_hostname in self.l:
            new_hostname = f"bkj-{''.join(random.choices(string.hexdigits, k=8)).upper()}"
        return new_hostname
