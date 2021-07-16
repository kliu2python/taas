import base64
import binascii

import pyotp
from Crypto.Cipher import AES

DEFAULT_AES_KEY = "1234567890123456"
SECRET_IV = "fortitokenmobile"


class BlockCipher(object):
    block_size = None

    @classmethod
    def encrypt(cls, raw, key=None):
        raise NotImplementedError

    @classmethod
    def decrypt(cls, encrypted, key, iv):
        raise NotImplementedError

    @classmethod
    def pad(cls, s):
        pad_len = cls.block_size - len(s) % cls.block_size
        return s + pad_len * chr(pad_len)

    @classmethod
    def unpad(cls, s):
        return s[0:-s[-1]]


class SeedAESCipher(BlockCipher):
    """
    AES cipher with CBC mode (block size 16 bytes).

    """
    block_size = AES.block_size
    IV = SECRET_IV

    @classmethod
    def encrypt(cls, raw, key=None):
        raw = cls.pad(raw)
        key = key[:16]
        cipher = AES.new(key, AES.MODE_CBC, cls.IV)
        cipher_text = cipher.encrypt(raw)
        return base64.b64encode(cipher_text)

    @classmethod
    def decrypt(cls, data, key=None, iv=None):
        data_b64 = base64.b64decode(data)
        key = key[:16]
        iv = iv or cls.IV
        cipher = AES.new(key, AES.MODE_CBC, iv)
        raw = cipher.decrypt(data_b64)
        return cls.unpad(raw)


class OneTimePassword(object):

    @classmethod
    def handler(cls, seed, otp, otplength=6, interval=30,
                algorithm='TOTP', count=None, func='verify',
                valid_window=None):
        result = None
        _seed = base64.b32encode(binascii.unhexlify(seed))
        if not isinstance(otplength, int):
            otplength = int(otplength)
        if not isinstance(interval, int):
            interval = int(interval)

        if algorithm == 'HOTP' and count is not None:
            handler = getattr(pyotp, algorithm)(_seed, digits=otplength)
            if func == 'verify':
                result = handler.verify(otp, count)
            elif func == 'generate':
                result = handler.at(count)
        else:
            handler = getattr(pyotp, algorithm)(_seed, digits=otplength,
                                                interval=interval)
            if func == 'verify':
                result = handler.verify(otp, valid_window=valid_window or 2)
            elif func == 'generate':
                result = handler.now()
        return result

    @classmethod
    def verify(cls, seed, otp, otplength=6, interval=30,
               algorithm='TOTP', count=None, func='verify', valid_window=2):
        return cls.handler(seed, otp, otplength, interval,
                           algorithm, count, func, valid_window)

    @classmethod
    def generate(cls, seed, otplength=6, interval=30,
                 algorithm='TOTP', count=None, func='generate'):
        return cls.handler(seed, None, otplength, interval,
                           algorithm, count, func)
