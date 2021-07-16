import json

import redis

from utils.logger import get_logger

logger = get_logger()


class DataStore:
    def __init__(self, keys, redis_conn: redis.Redis, identifier=None):
        self.identifier = identifier
        self.redis = redis_conn
        self.supported_keys: dict = keys

    def craft_key(self, key, identifier=None):
        iden = self.identifier
        if identifier:
            iden = identifier
        return f"{iden}_{key}" if iden else key

    def decraft_key(self, key, identifier=None):
        iden = self.identifier
        if identifier:
            iden = identifier
        return key.replace(f"{iden}_", "") if iden else key

    def get(self, key, identifier=None, default=None):
        dt = self.supported_keys.get(key)
        if dt:
            k = self.craft_key(key, identifier)
            ret = None
            if dt in [str]:
                ret = self.redis.get(k)
            elif dt in [int, float]:
                ret = self.redis.get(k)
                if ret:
                    if "." in ret:
                        ret = float(ret)
                    else:
                        ret = int(ret)
            elif dt is list:
                ret = self.redis.lrange(k, 0, -1)
            elif dt is set:
                ret = list(self.redis.smembers(k))
            elif dt is dict:
                ret = json.loads(self.redis.get(k))
            if not ret:
                return default
            return ret

        raise TypeError(f"unsupported data type {dt}")

    def mget(self, keys, identifier=None):
        result = {}
        for key in keys:
            result[key] = self.get(key, identifier)
        return result

    def set(self, key, value, identifier=None):
        dt = self.supported_keys.get(key)
        if dt:
            k = self.craft_key(key, identifier)
            if dt in [str, int, float]:
                if type(value) in [str, int, float]:
                    self.redis.set(k, value)
                else:
                    logger.error(
                        f"can not write to redis for {k} "
                        f"with value: {value}, data type not match"
                    )
            elif dt is list:
                if isinstance(value, list):
                    self.redis.rpush(k, *value)
                else:
                    logger.error(f"failed to add data for {k} with "
                                 f"value {value}, data type mismatch")
            elif dt is set:
                if isinstance(value, list):
                    self.redis.sadd(k, *value)
            elif dt is dict:
                self.redis.set(k, json.dumps(value))
            else:
                raise ValueError(f"failed to write to redis, type: {dt} not "
                                 f"supported")
        else:
            raise TypeError(f"unsupported data type {dt}")

    def mset(self, set_dict, identifier=None):
        for k, v in set_dict.items():
            self.set(k, v, identifier)

    def _incr_decr(self, key, amount: int, increase=True, identifier=None):
        dt = self.supported_keys.get(key)
        if dt is int:
            k = self.craft_key(key, identifier)
            if increase:
                self.redis.incr(k, amount)
            else:
                self.redis.decr(k, amount)
        else:
            raise TypeError(f"key data type {dt} is not int")

    def incr(self, key, amount: int, identifier=None):
        self._incr_decr(key, amount, identifier=identifier)

    def decr(self, key, amount: int, identifier=None):
        self._incr_decr(key, amount, increase=False, identifier=identifier)

    def exists(self, key, identifier=None):
        k = self.craft_key(key, identifier)
        return self.redis.exists(k)

    def lpop(self, key, identifier=None):
        k = self.craft_key(key, identifier)
        return self.redis.lpop(k)

    def rpoplpush(self, src, dst, identifier=None):
        k_src = self.craft_key(src, identifier)
        k_dst = self.craft_key(dst, identifier)
        return self.redis.rpoplpush(k_src, k_dst)

    def rpush(self, key, value, identifier=None):
        k = self.craft_key(key, identifier)
        return self.redis.rpush(k, value)

    def smove(self, src, dst, value, identifier=None):
        k_src = self.craft_key(src, identifier)
        k_dst = self.craft_key(dst, identifier)
        return self.redis.smove(k_src, k_dst, value)

    def smembers(self, key, identifier=None):
        k = self.craft_key(key, identifier)
        return self.redis.smembers(k)

    def spop(self, key, count=1, identifier=None):
        k = self.craft_key(key, identifier)
        return self.redis.spop(k, count)

    def scard(self, key, identifier=None):
        k = self.craft_key(key, identifier)
        return self.redis.scard(k)

    def keys(self, key_pattern, identifier=None):
        k = self.craft_key(key_pattern, identifier)
        return self.redis.keys(k)

    def delete(self, key, identifier=None):
        k = self.craft_key(key, identifier)
        return self.redis.delete(k)
