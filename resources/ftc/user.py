import re

import requests

import resources.constants as constants
import resources.ftc.otp as otp
from resources.ftc.clients import FTMClient
from resources.ftc.db import FtcDatabase, Tables
from utils.logger import get_logger

logger = get_logger()


class User:
    @classmethod
    def _add_membership(cls, users, group, ssh_client=None):
        logger.info(f"Adding group for {len(users)} users")
        users = " ".join(users)
        command = [
            "config user group",
            f"edit {group}",
            f"append member {users}",
            "end"
        ]
        ssh_client.send_commands(command, timeout=300)

    @classmethod
    def _add_membership_api(cls, users, data):
        end_point = f"api/v2/cmdb/user/group/{data.get('group')}"
        user_list = [{"name": user} for user in users]
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "member": user_list
        }
        params = {
            "vdom": data.get("vdom"),
            "access_token": data.get("fgt_token")
        }
        resp = requests.put(
            url=f"https://{data.get('ip')}/{end_point}",
            headers=headers,
            params=params,
            verify=False,
            json=payload,
            timeout=30
        )
        assert resp.status_code == 200, resp.text

    @classmethod
    def _delete_membership(cls, group, ssh_client=None):
        command = [
            "config user group",
            f"edit {group}",
            "unset member",
            "end"
        ]
        ssh_client.send_commands(command)

    @classmethod
    def _get_db_connection(cls, data):
        return FtcDatabase(
            db_ip=data.get("db_ip"),
            db_name=data.get("db_name"),
            db_user=data.get("db_user"),
            db_pw=data.get("db_pw")
        )

    @staticmethod
    def _activate_token(user, ftc_data, db):
        ftm_client = FTMClient(
            ftc_server=ftc_data.get("ftc_server"),
            cert_path=ftc_data.get("cert_path"),
            key_path=ftc_data.get("key_path")
        )
        if ftc_data.get("mfa_device", "android") in ["android"]:
            ftm_info = constants.FTM_ANDRIOD
        else:
            ftm_info = constants.FTM_IOS
        retry = 5
        while retry > 0:
            try:
                ftm_client.activate_user(user, db, ftm_info)
                return
            except Exception as err:
                logger.info(f"Error when try to active user {user}")
                retry -= 1
                if retry <= 0:
                    raise err

    @staticmethod
    def _get_seed(user_name, db):
        user_id = db.query(Tables.USERS, "username", user_name)
        tokens = db.query(Tables.TOKENS, "user_id", user_id[0].get("id"))
        return tokens[0].get("_seed")

    def register_mfa(self, users, data):
        users_data = []
        ftc_data = data.get("ftc")
        mfa_provider = data.get("mfa_provider")
        db = None
        failed = []
        if ftc_data:
            db = self._get_db_connection(ftc_data)

        for user in users:
            try:
                user_dict = {
                    "password": data.get("user_password"),
                    "custom_data": data.get("custom_data", None)
                }
                if user.startswith("<"):
                    match = re.search(r">(.*?)<", user).group(1)
                    user_dict["user"] = match
                else:
                    user_dict["user"] = user
                if ftc_data and mfa_provider in ["fortitoken-cloud"]:
                    if ftc_data.get("mfa_type") in ["ftm", "FTM"]:
                        logger.info(f"Activate token for user: {user}")
                        self._activate_token(user, ftc_data, db)
                        seed = self._get_seed(user, db)
                        seed = otp.SeedAESCipher().decrypt(
                            data=seed.encode("utf8"),
                            key=otp.DEFAULT_AES_KEY.encode("utf8"),
                            iv=otp.SECRET_IV.encode("utf8")
                        )
                        user_dict["seed"] = seed.decode()
                users_data.append(user_dict)
            except Exception as e:
                logger.exception("Error when fetch data", exc_info=e)
                failed.append(user)
        if db:
            db.close()
        return users_data, failed
