import io
import os
import re

import ftplib

from fos.conf import CONF
from utils.logger import get_logger

IMAGE_PATH = "Images/{product}/{version}/images/"
LOGGER = get_logger()
CONF = CONF["infosite"]


class InfoSiteClient:
    def __init__(self):
        self.ftp_client = ftplib.FTP(CONF["ftp_ip"])
        self._user = CONF["ftp_user"]
        self._password = CONF["ftp_password"]
        self._curr_dir = None
        self._in_progress = set()

    def login(self):
        self.ftp_client.login(self._user, self._password)

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()

    def set_build(self, build="0", product="FortiOS", version="v7.00"):
        """
        Set build number for client, by default it will be latest. for now
        we only support latest.
        """
        if build in ["0", 0]:
            path = IMAGE_PATH.format(product=product, version=version)
            self._go_to_dir(path)
            dirs = self.ftp_client.nlst()

            ret = 0
            latest_path = None
            for d in dirs:
                build_re = re.search(r"\d+", d)
                if build_re:
                    number = int(build_re.group(0))
                    if number > ret:
                        ret = number
                        latest_path = d
            self.ftp_client.cwd(latest_path)
            self._curr_dir = os.path.join(path, latest_path)
        else:
            raise NotImplementedError(
                "set to none latest build is not supported yet"
            )

    def download(self, file_name, dir_name=None, stream=True):
        if dir_name:
            file_path = os.path.join(dir_name, file_name)
        else:
            file_path = file_name
        try:
            if stream:
                with io.BytesIO() as BUF:
                    self.ftp_client.retrbinary(f"RETR {file_name}", BUF.write)
                    data = BUF.getvalue()
                return data
            else:
                if file_path not in self._in_progress:
                    self._in_progress.add(file_path)

                    with open(file_path, "wb") as F:
                        self.ftp_client.retrbinary(f"RETR {file_name}", F.write)
                else:
                    LOGGER.info(
                        "Another Downloading is in progress, please try again"
                    )
        except Exception as e:
            LOGGER.exception(
                f"Error when download file {file_name}", exc_info=e
            )
            file_path = None
        finally:
            if not stream:
                self._in_progress.remove(file_path)

        return file_path

    def _go_to_dir(self, full_path):
        for path in full_path.split("/"):
            self.ftp_client.cwd(path)

    def quit(self):
        self.ftp_client.quit()


if __name__ == "__main__":
    client = InfoSiteClient()
    client.login()
    client.set_build()
    client.download("platform.xml")
    client.quit()
