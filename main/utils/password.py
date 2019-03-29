import os
import hashlib


def generate_salt():
    return os.urandom(8).hex()


def generate_hash(password, salt):
    h = hashlib.sha256()
    h.update(salt.encode('utf-8'))
    h.update(password.encode('utf-8'))
    return h.hexdigest()
