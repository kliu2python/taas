import os
import re
from urllib.parse import urlparse

import requests

from utils.ftp import FtpClient
from utils.logger import get_logger

logger = get_logger()


def http_download(url, dst, cookies=None):
    filename = url.split('/')[-1]
    filename = os.path.join(dst, filename)
    logger.info(f"Downloading file {filename}")
    with requests.get(url, stream=True, cookies=cookies) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    if os.path.exists(filename):
        return filename
    raise FileNotFoundError(f"Failed to download {filename}")


def download(url, **kwargs):
    uri = urlparse(url)
    proto = uri.scheme
    dst = kwargs.pop("dst")
    regex = kwargs.pop("regex")
    kwargs.pop("ip")
    if "http" in proto:
        return http_download(url, dst)
    elif "ftp" in proto:
        with FtpClient(uri.netloc, **kwargs) as FTP:
            if regex:
                file_path = None
                file_name = re.compile(uri.path.split("/")[-1])
                file_dir = os.path.dirname(uri.path)
                FTP.ftp_client.cwd(file_dir)
                for file in FTP.ftp_client.nlst():
                    matches = file_name.match(file)
                    if matches:
                        file_name = file
                        file_path = f"{file_dir}/{file_name}"
                        break
            else:
                file_path = uri.path

            logger.info(f"Downloading file {file_path}")
            if file_path:
                FTP.download_file(file_path, dst)
                dst_file = os.path.join(dst, file_name)
                if os.path.exists(dst_file):
                    return dst_file
            raise FileNotFoundError(f"File not found for {file_path}")
    else:
        raise RuntimeError(f"Unsupported Protocal {proto}")
