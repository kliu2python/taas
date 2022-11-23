import re

import requests

from upgrade.cache import Cache
from utils.logger import get_logger

cache = Cache()
logger = get_logger()
INFOSITE_DATA_URL = "http://10.160.19.9/fos_all.txt"


def get_key(repo, release):
    return f"___{repo}_{release}"


def set_cache(data, key):
    cache.set("infosite_builds", data, key)


def get_cache(key):
    return cache.get("infosite_builds", key)


def update_cache():
    resp = requests.get(INFOSITE_DATA_URL)
    if resp.status_code in [200]:
        data = resp.text
        data = data.split("\n")

        interm_builds = []
        release = ""
        for line in data:
            logger.info(f"Update build: {line}")
            if line:
                line = line.split(",")
                repo = line[0].strip()
                ver = line[1].strip()
                build = int(line[2].strip())

                if ver in ["Interim Build"]:
                    interm_builds.append(build)
                else:
                    if interm_builds:
                        key = get_key(repo, release)
                        set_cache(interm_builds, key)
                        interm_builds = []

                    release = ver.replace("Release", "").replace(" ", "")
                    release = release.replace("v", "").lower()
                    key = get_key(repo, release)
                    set_cache([build], key)
                    interm_builds.append(build)

                    release = re.search(r"(.*)(.[a-z])", release).group(1)


if __name__ == "__main__":
    from time import sleep
    while True:
        update_cache()
        sleep(10)
