import os
import re
from copy import deepcopy

from upgrade.conf import CONF
from upgrade.base import Updater
from upgrade.fos.ssh import FgtSsh
from upgrade.infosite import get_cache
from upgrade.infosite import get_key
from utils.infosite import InfoSiteFtpClient


class FosUpdater(Updater, FgtSsh):
    def update(self, req_id, data):
        infosite = CONF["infosite"]
        build_info = data.get("build_info")
        conf = deepcopy(CONF)
        dst = conf["ftp"].pop("dst_dir")
        dst = os.path.join(dst, req_id)
        repo, file_name = self._get_build_info(
            build_info.get("repo"),
            build_info.get("file_pattern")
        )
        build_info["repo"] = repo
        build_info = self.determin_build(build_info)
        with InfoSiteFtpClient(**infosite) as client:
            file = client.download(
                file_name=file_name, dst_dir=dst, **build_info
            )
        if file:
            file_restore = os.path.join(req_id, file[-1])
            self.restore_binary(file_restore, build_info["type"], **conf["ftp"])
            _, version = self.get_model_version()
            return file, version
        else:
            raise FileNotFoundError(
                f"{build_info['type']} file not found to upgrade"
            )

    def _get_build_info(self, repo, file_pattern=None):
        if file_pattern:
            return repo, file_pattern
        else:
            return self.get_device_info(repo)

    def determin_build(self, build_info):
        release = str(build_info.get("release"))
        if release:
            print(release)
            matches = re.search(r"^(\d+).(\d+).(\d+)", release)
            if matches:
                build_info["version"] = f"v{matches.group(1)}.00"
                if build_info.get("build") == 0:
                    repo = build_info.get("repo")
                    key = get_key(repo, release.lower())
                    build_list = get_cache(key)
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
