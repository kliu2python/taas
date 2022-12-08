import ftplib
import os
import io

from utils.logger import get_logger

LOGGER = get_logger()


class FtpClient:
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

    def download_file(self, file_path, save_path):
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

    def quit(self):
        self.ftp_client.quit()
