import ftplib
import io
import os
import re

from utils.logger import get_logger

LOGGER = get_logger()


class InfoSiteFtpClient:
    IMAGE_PATH = "/home/Images/{repo}/{version}/images"

    def __init__(self, ip, user, password):
        self.ftp_client = ftplib.FTP(ip)
        self._user = user
        self._password = password

    def login(self):
        self.ftp_client.login(self._user, self._password)

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()

    def _download_build(self, path, file_regx, dst_dir, desired_build):
        build = 0
        latest_path = None
        dirs = self.ftp_client.nlst(path)

        if not dirs:
            return None

        for d in dirs:
            build_re = re.search(r"\d+$", d)
            if build_re:
                number = int(build_re.group(0))
                if desired_build == 0:
                    if number > build:
                        build = number
                        latest_path = d
                elif desired_build == number:
                    latest_path = d
                    break
        if not latest_path:
            raise FileNotFoundError(
                f"Failed to fine target build:{desired_build}, path: {path}"
            )

        try:
            ret = []
            files = self.ftp_client.nlst(latest_path)
            for file in files:
                if re.search(file_regx, file):
                    LOGGER.info(f"Downloading file: {file}")
                    content = self._do_download(file, dst_dir)
                    ret.append(content)
            return ret
        except Exception as e:
            LOGGER.exception(
                f"Error when download laetst build {path}", exc_info=e
            )

    def _do_download(self, file_path, save_path):
        file_name = os.path.basename(file_path)

        if save_path:
            target = open(os.path.join(save_path, file_name), "wb")
        else:
            target = io.BytesIO()

        with target as BUF:
            self.ftp_client.retrbinary(
                f"RETR {file_path}", BUF.write
            )
            return file_name

    def download(
            self,
            repo: str,
            version: str,
            branch: str,
            file_name: str,
            dst_dir: str = None,
            build: int = 0,
            **kwargs
    ):
        """
        download latest version or specified version of image

        :param repo: FortiProduct, this should be the path in 172.16.100.71
        e.g. ForitOS , FortiOS-6K7K should be shown on infosite
        :type repo: str

        :param version: major version to download, should shshould be in ftp
        path of 172.16.100.71
        :type version: str

        :param branch: list of branches to check and download
        :type branch: str

        :param file_name: regx of file name to download
        e.g. r"platform\-*(.+)*.xml$"
        :type file_name: str

        :param dst_dir: folder to save for downloaded file, if this is none
        this function will return file content directly.
        :type dst_dir: str

        :param build: folder to save for downloaded file, if this is none
        this function will return file content directly.
        :type build: int

        :return: file names
        :rtype: list
        """
        path = self.IMAGE_PATH.format(repo=repo, version=version)

        LOGGER.info(f"{kwargs} parameters will be ignored")

        if branch.lower() not in ["", "main"]:
            path = f"{path}/NoMainBranch/{branch}"
        file = self._download_build(path, file_name, dst_dir, build)
        return file

    def quit(self):
        self.ftp_client.quit()


if __name__ == "__main__":
    with InfoSiteFtpClient("172.16.100.71", "znie", "xxxxx") as info_client:
        res = info_client.download(
            "FortiOS",
            "v7.00",
            "fg_7-0_3000f",
            "FGT_3001F-(.*)-build(.*)-FORTINET.out$",
            r"C:\Users\znie\Downloads",
            0
        )
        print(res)
