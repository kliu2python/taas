import os
from copy import deepcopy

from upgrade.conf import CONF
from utils.infosite.ftp import InfoSiteFtpClient
from upgrade.base import Updater
from upgrade.fos.ssh import FgtSsh


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


