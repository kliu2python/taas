import os
import re
from copy import deepcopy

from upgrade.caches import ImageCache
from upgrade.conf import CONF
from upgrade.base import Updater
from upgrade.fos.ssh import FgtSsh
from upgrade.infosite import get_build_cache
from upgrade.infosite import get_key
from utils.infosite import InfoSiteFtpClient

image_cache = ImageCache()
KEY_PREFIX = "__image"


class FosUpdater(Updater, FgtSsh):
    @classmethod
    def _get_image_cache_key(cls, build_info):
        build_info = [
            KEY_PREFIX,
            build_info["repo"],
            build_info["version"],
            build_info["branch"],
            build_info["build"]
        ]
        return "_".join(build_info)

    @classmethod
    def update_image_cache(cls, build_info, file):
        k = cls._get_image_cache_key(build_info)
        image_cache.set("file", file, k)

    @classmethod
    def get_image_from_cache(cls, build_info):
        if build_info.get("use_cache", True):
            k = cls._get_image_cache_key(build_info)
            return image_cache.get("file", k)

    def update(self, req_id, data):
        infosite = CONF["infosite"]
        build_info = data.get("build_info")
        conf = deepcopy(CONF)
        dst = conf["ftp"].pop("dst_dir")
        dst = os.path.join(dst, req_id)
        repo, file_name = self._get_build_info(
            build_info.get("repo"),
            build_info.get("file_pattern"),
            build_info.get("debug", False)
        )
        build_info["repo"] = repo
        build_info = self.determin_build(build_info)
        cached = self.get_image_from_cache(build_info)
        if cached:
            file = cached
        else:
            with InfoSiteFtpClient(**infosite) as client:
                file = client.download(
                    file_name=file_name, dst_dir=dst, **build_info
                )
        if file:
            file_restore = os.path.join(req_id, file[-1])
            if not cached:
                self.update_image_cache(build_info, file_restore)
            self.restore_binary(file_restore, build_info["type"], **conf["ftp"])
            _, version = self.get_model_version()
            ret = {
                "used_file": file,
                "current_build": version,
                "expect_build": build_info["build"]
            }
            if data.get("verify", True):
                if build_info["type"] in ["image"]:
                    if build_info["build"] not in version:
                        raise Exception(
                            f"Upgrade Failed! "
                            f"Expect build: Curr Version: {version}"
                            f"File: {file}"
                        )
                else:
                    ret["warning"] = (f"Post upgrade verify Not support yet for"
                                      f" type {build_info['type']} "
                                      f"Currently Only support "
                                      f"image version check")
            return ret
        else:
            raise FileNotFoundError(
                f"{build_info['type']} file not found to upgrade"
            )

    def _get_build_info(self, repo, file_pattern=None, debug=False):
        if file_pattern:
            return repo, file_pattern
        else:
            repo, file_pattern = self.get_device_info(repo)
            if debug:
                file_pattern = file_pattern.replace(".out", ".deb")
            return repo, file_pattern

    @staticmethod
    def determin_build(build_info):
        release = str(build_info.get("release"))
        if release:
            matches = re.search(r"^(\d+).(\d+).(\d+)", release)
            if matches:
                build_info["version"] = f"v{matches.group(1)}.00"
                if build_info.get("build") == 0 and not build_info["branch"]:
                    repo = build_info.get("repo")
                    key = get_key(repo, release.lower())
                    build_list = get_build_cache(key)
                    if build_list:
                        build = max(build_list)
                        build_info["build"] = build
                    else:
                        raise Exception(f"latest build for {release} "
                                        f"does not exists")
                return build_info

            matches = re.search(r"^(\d+)$", release)
            if matches:
                build_info["version"] = f"v{release}.00"
                return build_info
            raise Exception("release value is not in correct format, "
                            "For trunk branch, use single digits like 7 or 6"
                            "For Release, use like 7.0.1")
