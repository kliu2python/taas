import json
import os
import pickle

import yaml

from taascli.conf import get_config


class PrintInColor:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    LIGHT_PURPLE = '\033[94m'
    PURPLE = '\033[95m'
    END = '\033[0m'

    @classmethod
    def red(cls, s, **kwargs):
        msg = f"{cls.RED}{s}{cls.END}"
        print(msg, **kwargs)
        return msg

    @classmethod
    def green(cls, s, **kwargs):
        msg = f"{cls.GREEN}{s}{cls.END}"
        print(msg, **kwargs)

    @classmethod
    def yellow(cls, s, **kwargs):
        msg = f"{cls.YELLOW}{s}{cls.END}"
        print(msg, **kwargs)

    @classmethod
    def lightpurple(cls, s, **kwargs):
        msg = f"{cls.LIGHT_PURPLE}{s}{cls.END}"
        print(msg, **kwargs)

    @classmethod
    def purple(cls, s, **kwargs):
        msg = f"{cls.PURPLE}{s}{cls.END}"
        print(msg, **kwargs)


def dict_print(msg_dit):
    return yaml.dump(msg_dit)


def get_api_url(api_path, port=None):
    config = get_config()
    if port:
        url_port = port
    else:
        url_port = 8000
    return f"http://{config['server_ip']}:{url_port}/{api_path}"


def load_file(args):
    file = args.file
    if file:
        if os.path.exists(file):
            extension = os.path.splitext(file)[1]
            with open(file) as F:
                if extension in [".json"]:
                    data = json.load(F)
                elif extension in [".yaml", ".yml"]:
                    content = yaml.safe_load_all(F)
                    data = []
                    for con in content:
                        data.append(con)
                else:
                    raise TypeError("Only .json, .yaml, .yml file supported")
        else:
            raise FileExistsError(f"file {args.file} does not exists")
        return data


def save_pickle(data, path):
    with open(path, "wb") as F:
        pickle.dump(data, F)


def load_pickle(path):
    with open(path, "rb") as F:
        data = pickle.load(F)
    return data
