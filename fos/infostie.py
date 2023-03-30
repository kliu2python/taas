import ftplib
import io
import re
from collections import OrderedDict


from fos.conf import CONF
from fos.platforms import Fortigate
from utils.logger import get_logger
from utils.mongodb import MongoDB

IMAGE_PATH = "/home/Images/{product}/{version}/images"
LOGGER = get_logger()
REF_FILE = r"platform\-*(.+)*.xml$"


class InfoSiteClient:
    def __init__(self):
        self.ftp_client = ftplib.FTP(CONF["infosite"]["ftp_ip"])
        self._user = CONF["infosite"]["ftp_user"]
        self._password = CONF["infosite"]["ftp_password"]
        self._builds = []
        self._db = MongoDB(CONF.get("db"), CONF.get("default_db", "fos"))

    def login(self):
        self.ftp_client.login(self._user, self._password)

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()

    def _download_latest_build(self, product, version, branch, path):
        build = 0
        cache = OrderedDict()
        dirs = self.ftp_client.nlst(path)

        for d in dirs:
            build_re = re.search(r"\d+$", d)
            if build_re:
                number = int(build_re.group(0))
                if number > build:
                    build = number
                    latest_path = d
                    cache[number] = latest_path

        if not dirs:
            return None

        try:
            major_version = re.search(r"v(.)\.", version).group(1)
            while cache:
                data = cache.popitem()
                versions_db = {
                    "major_version": major_version,
                    "build": str(data[0]),
                    "branch": branch
                }
                if not self._db.find(versions_db, "versions"):
                    LOGGER.info(f"Adding {versions_db}")
                    file_path = f"{data[1]}"
                    files = self.ftp_client.nlst(file_path)
                    updated = False
                    for file in files:
                        if re.search(REF_FILE, file):
                            content = self._do_download(file)
                            file = file.split("/")[-1]
                            LOGGER.info(f"File: {file}")
                            d = {
                                "product": product,
                                "version": version,
                                "branch": branch,
                                "build": data[0],
                                "file": file,
                                "data": content
                            }
                            Fortigate(d).update()
                            updated = True
                    if updated:
                        break
                else:
                    LOGGER.info(f"Build version {versions_db}exists, skipping")
                    break
        except Exception as e:
            LOGGER.exception(
                f"Error when download laetst build {path}", exc_info=e
            )

    def _do_download(self, file_path):
        with io.BytesIO() as BUF:
            self.ftp_client.retrbinary(
                f"RETR {file_path}", BUF.write
            )
            data = BUF.getvalue()
        return data.decode()

    def download(
            self,
            product="FortiOS",
            version="v7.00"
    ):
        ret = []
        path = IMAGE_PATH.format(product=product, version=version)

        self._download_latest_build(product, version, "", path)

        branches = self.ftp_client.nlst(f"{path}/NoMainBranch")
        for branch in branches:
            branch_name = branch.split("/")[-1]
            self._download_latest_build(
                product, version, branch_name, branch
            )

        return ret

    def quit(self):
        try:
            self.ftp_client.quit()
        except EOFError:
            LOGGER.warning("EOF error for closing FTP client!")


if __name__ == "__main__":
    # To Drop all collections, run uncomments following three lines
    db = MongoDB(CONF.get("db"), CONF.get("default_db", "fos"))
    for x in ["versions", "models", "platforms", "features"]:
        db.drop_collection(CONF.get("default_db", "fos"), x)
    # client = InfoSiteClient()
    # client.login()
    # client.download()
    # client.quit()
