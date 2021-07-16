from typing import Union

DEFAULT_AES_KEY : str
SECRET_IV : str


class BlockCipher:
    block_size : int

    @classmethod
    def encrypt(cls, raw, key=None) -> bytes: ...

    @classmethod
    def decrypt(cls, encrypted, key, iv) -> str: ...

    @classmethod
    def pad(cls, s) -> Union[bytes, bytearray, memoryview]: ...

    @classmethod
    def unpad(cls, s) -> str: ...


class SeedAESCipher(BlockCipher):
    block_size : int
    IV : Union[bytes, bytearray, memoryview]

    @classmethod
    def encrypt(cls, raw, key=None) -> bytes: ...

    @classmethod
    def decrypt(cls, data, key=None, iv=None) -> str: ...


class OneTimePassword(object):

    @classmethod
    def handler(cls, seed, otp, otplength: int, interval: int,
                algorithm: str, count: int , func: str,
                valid_window=None) -> str: ...

    @classmethod
    def verify(cls, seed, otp, otplength: int, interval: int,
               algorithm: str, count: int, func: str, valid_window: int
    ) -> str: ...

    @classmethod
    def generate(cls, seed, otplength: int = 6, interval: int = 30,
                 algorithm: str = "", count: int = None, func: str = ""
    ) -> str: ...