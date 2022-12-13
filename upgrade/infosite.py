import os
import re

import requests

from upgrade.caches import InfositeCache
from upgrade.statics import update_total_build_query
from utils.logger import get_logger

cache = InfositeCache()
logger = get_logger()
DATA_IP = os.environ.get("DATA_IP", "10.160.19.9")
INFOSITE_DATA_URL = f"http://{DATA_IP}/fos_all.txt"
KEY_PREFIX = "__infosite"


def get_key(repo, release):
    return f"{KEY_PREFIX}_{repo}_{release}"


def set_build_cache(data, key):
    cache.set("builds", data, key)


def get_build_cache(key):
    return cache.get("builds", key)


def get_release_cache():
    update_total_build_query()
    return cache.get("releases", KEY_PREFIX)


def update_cache():
    resp = requests.get(INFOSITE_DATA_URL)
    if resp.status_code in [200]:
        data = resp.text
        data = data.split("\n")

        interm_builds = []
        releases = []
        release = ""
        for line in data:
            if line:
                logger.info(f"Update build: {line}")
                if "Release" in line:
                    releases.append(line)
                line = line.split(",")
                repo = line[0].strip()
                ver = line[1].strip()
                build = int(line[2].strip())

                if ver in ["Interim Build"]:
                    interm_builds.append(build)
                else:
                    if interm_builds:
                        key = get_key(repo, release)
                        set_build_cache(interm_builds, key)
                        interm_builds = []

                    release = ver.replace("Release", "").replace(" ", "")
                    release = release.replace("v", "").lower()
                    key = get_key(repo, release)
                    set_build_cache([build], key)
                    interm_builds.append(build)

                    release = re.search(r"(.*)(.[a-z])", release).group(1)
        cache.replace("releases", releases, KEY_PREFIX)


if __name__ == "__main__":
    from time import sleep
    while True:
        update_cache()
        sleep(1800)
