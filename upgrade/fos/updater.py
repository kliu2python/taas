import os
import re
from copy import deepcopy

from upgrade.caches import ImageCache
from upgrade.conf import CONF
from upgrade.base import Updater
from upgrade.fos.ssh import FgtSsh
from upgrade.fos.pkgs import PKGS
from upgrade.infosite import get_build_cache
from upgrade.infosite import get_key
from utils.files import download
from utils.infosite import InfoSiteFtpClient
from utils.logger import get_logger

image_cache = ImageCache()
logger = get_logger()
KEY_PREFIX = "__image"


class FosUpdater(Updater, FgtSsh):
    @classmethod
    def _get_image_cache_key(cls, build_info):
        build_info = [
            KEY_PREFIX,
            build_info["repo"],
            build_info["version"],
            build_info["branch"],
            str(build_info["build"])
        ]
        return "_".join(build_info)

    @classmethod
    def _update_image_cache(cls, build_info, file):
        k = cls._get_image_cache_key(build_info)
        image_cache.set("file", file, k)

    @classmethod
    def _get_image_from_cache(cls, build_info):
        if build_info.get("use_cache", True):
            k = cls._get_image_cache_key(build_info)
            return image_cache.get("file", k)

    def _get_image(self, req_id, dst, build_info):
        infosite = CONF["infosite"]
        repo, file_name = self._get_build_info(
            build_info.get("repo"),
            build_info.get("file_pattern"),
            build_info.get("debug", False)
        )
        build_info["repo"] = repo
        build_info = self._determin_build(build_info)
        cached = self._get_image_from_cache(build_info)
        if cached:
            logger.info(f"Found cached image: {cached}")
            file = cached
        else:
            logger.info(f"Target build not found in cache, downloading now")
            with InfoSiteFtpClient(**infosite) as client:
                file = client.download(
                    file_name=file_name, dst_dir=dst, **build_info
                )
        if file:
            if cached:
                file_restore = file
                file = file_restore.split("/")[-1]
            else:
                file_restore = os.path.join(req_id, file[-1])
                self._update_image_cache(build_info, file_restore)
            return file, file_restore

    def _get_build_info(self, repo, file_pattern=None, debug=False):
        if file_pattern:
            return repo, file_pattern
        else:
            repo, file_pattern = self.get_device_info(repo)
            if debug:
                file_pattern = file_pattern.replace(".out", ".deb")
            return repo, file_pattern

    @classmethod
    def _get_latest_build(cls, build_info, release):
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

    @classmethod
    def _determin_build(cls, build_info):
        release = str(build_info.get("release"))
        if release:
            matches = re.search(r"^(\d+).(\d+).(\d+)", release)
            if matches:
                build_info["version"] = f"v{matches.group(1)}.00"
                build_info = cls._get_latest_build(build_info, release)
                return build_info

            matches = re.search(r"^(\d+)$", release)
            if matches:
                build_info["version"] = f"v{release}.00"
                return build_info
            raise Exception("release value is not in correct format, "
                            "For trunk branch, use single digits like 7 or 6"
                            "For Release, use like 7.0.1")

    @classmethod
    def _verify_image_upgrade(cls, build_info, version):
        if build_info["build"] not in version:
            raise Exception(
                f"Upgrade Failed! "
                f"Expect build: Curr Version: {version}"
            )

    def upgrade_image(self, req_id, data):
        build_info = data.get("build_info")
        conf = deepcopy(CONF)
        dst = os.path.join(conf["ftp"].pop("dst_dir"), req_id)
        os.makedirs(dst, exist_ok=True)
        file, file_restore = self._get_image(req_id, dst, build_info)
        if file:
            self.restore_binary(file_restore, "image", **conf["ftp"])
            _, version = self.get_model_version()
            ret = {
                "used_file": file,
                "current_build": version,
                "expect_build": build_info["build"]
            }
            if data.get("verify", True):
                self._verify_image_upgrade(build_info, version)
            return ret, True
        else:
            raise FileNotFoundError(
                f"{build_info['type']} file not found to upgrade"
            )

    @classmethod
    def _download_pkg(cls, pkg_type, file_type, release, build, **kwargs):
        pkg_def = PKGS.get(pkg_type)
        if pkg_def:
            file_path_template = f"{pkg_def['url']}/{pkg_def['file_name']}"
            file_info = {
                "file": file_type,
                "release": release,
                "build": build,
                "file_cap": file_type.upper(),
                "file_lower": file_type.lower()
            }
            file_path = file_path_template.format(**file_info)
            file = download(file_path, regex=pkg_def.get("regex"), **kwargs)
            return {"cmd_type": pkg_def["cmd_type"], "file": file}
        else:
            raise Exception(f"package type {pkg_type} is not defined")

    def _upload_pkg(self, file, conf):
        status = True
        res = {}
        try:
            res["file"] = file["file"]
            self.restore_binary(
                file["file"], file["cmd_type"], **conf["ftp"], ignore_error=True
            )
            res["status"] = "OK"
        except Exception as e:
            res["status"] = "ERROR"
            res["error"] = str(e)
            status = False
        return res, status

    @classmethod
    def _get_upgrade_path(cls, req_id, file_path):
        file_name = os.path.basename(file_path)
        return os.path.join(req_id, file_name)

    @classmethod
    def _get_pkg_cache_key(cls, pkg_type, file_type, release, build):
        return f"{KEY_PREFIX}_{pkg_type}_{file_type}_{release}_{build}"

    @classmethod
    def _get_pkg_from_cache(cls, key):
        return image_cache.get("pkg", key)

    @classmethod
    def _update_pkg_cache(cls, path, key):
        image_cache.set("pkg", path, key)

    def upgrade_pkg(self, req_id, data):
        conf = deepcopy(CONF)
        dst = os.path.join(conf["ftp"].pop("dst_dir"), req_id)
        os.makedirs(dst, exist_ok=True)
        pkgs = data.get("build_info", {}).get("pkgs")
        if pkgs:
            result = {}
            status = True
            for pkg_type, builds in pkgs.items():
                pkg_res = {}
                for file_type, build in builds["builds"].items():
                    file_res = {}
                    try:
                        release = builds.get("release")
                        logger.info(
                            f"Getting cached pkg for "
                            f"{pkg_type}, {file_type}, {release}, {build}"
                        )
                        key = self._get_pkg_cache_key(
                            pkg_type, file_type, release, build
                        )
                        cached = self._get_pkg_from_cache(key)
                        if cached:
                            logger.info(f"using cached pkg {cached}")
                            file = cached
                        else:
                            logger.info("No Cached pkg found, now downloading")
                            file = self._download_pkg(
                                pkg_type, file_type, release, build,
                                dst=dst, **conf["infosite"]
                            )
                            if file:
                                file["file"] = self._get_upgrade_path(
                                    req_id, file["file"]
                                )
                                self._update_pkg_cache(file, key)
                            else:
                                raise Exception(f"Failed to download package")
                        out, sta = self._upload_pkg(file, conf)
                        file_res["result"] = out
                        if sta:
                            file_res["status"] = "completed"
                        else:
                            raise Exception(f"Failed to upgrade")
                    except Exception as e:
                        file_res["status"] = "failed"
                        file_res["error"] = str(e)
                        status = False
                    finally:
                        pkg_res[file_type] = file_res
                result[pkg_type] = pkg_res
            return result, status
        else:
            raise ValueError("no pkgs defined for pkg upgrade")

    def update(self, req_id, data):
        update_type = data["build_info"]["type"]
        func_name = f"upgrade_{update_type.lower()}"
        func = getattr(self, func_name)
        return func(req_id, data)


if __name__ == "__main__":
    test_data = {
        "platform": "fos",
        "build_info": {
            "type": "pkg",
            "pkgs": {
                "avsig": {
                    "release": "7.2.0",
                    "builds": {
                        "ETDB.High": "90.08471",
                        "FLDB": "90.08471",
                        "MMDB": "90.08471"
                    }
                },
                "aveng": {
                    "release": "7.00",
                    "builds": {
                        "vsigupdate": "0005"
                    }
                },
                "ipssig": {
                    "release": "7.2.0",
                    "builds": {
                        "isdb": "22.00450",
                        "nids": "22.00450",
                        "apdb": "22.00448"
                    }
                },
                "ipseng": {
                    "release": "7.00",
                    "builds": {
                        "flen": "0300"
                    }
                },
                "malware": {
                    "builds": {
                        "latestMalwareFile": "04.338"
                    }
                }
            },
            "verify": True,
            "force": True
        },
        "device_access": {
            "host": "10.160.16.191",
            "username": "admin",
            "password": "fortinet"
        }
    }
    r, s = FosUpdater(**test_data["device_access"]).update("test", test_data)
    print(r)
    print(s)
