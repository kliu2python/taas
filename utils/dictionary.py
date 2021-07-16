import collections.abc


def deep_update(d, u):
    for k, v in u.items():
        if k in d and isinstance(v, collections.abc.Mapping):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d
