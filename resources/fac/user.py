import base64
import requests

from resources.ftc.user import User as FtcUser
from resources.pool import ResourcePoolMixin
from utils.logger import get_logger

logger = get_logger()


class User(FtcUser, ResourcePoolMixin):
    @classmethod
    def _get_fac_api_url(cls, fac_ip, api_name):
        return f"https://{fac_ip}/api/v1/{api_name}/"

    @classmethod
    def _get_fac_auth_header(cls, username, password):
        return {
            "Authorization": "Basic {}".format(
                base64.b64encode(
                    bytes(
                        f"{username}"
                        f":{password}", "UTF-8")
                ).decode("ascii")
            ),
            "Content-Type": "application/json"
        }

    @classmethod
    def _check_and_delete_user(cls, api_url, auth_header, username):
        resp = requests.get(
            f"{api_url}?username={username}",
            headers=auth_header,
            verify=False
        )
        if resp.status_code == 200:
            user_ids = resp.json().get("objects", [])
            if user_ids:
                user_id = user_ids[0].get("id")
                if user_id:
                    resp = requests.delete(
                        f"{api_url}/{user_id}/",
                        headers=auth_header,
                        verify=False
                    )

                    if resp.status_code >= 400:
                        return f"{resp.status_code}{resp.text}"

    @classmethod
    def create_user(cls, data):
        created_user = []
        failed_user = []
        capacity = data.get("capacity")
        mfa_provider = data.get("mfa_provider")
        token_auth = False
        if mfa_provider in ["fortitoken-cloud"]:
            mfa_provider = "ftc"
            token_auth = True
        payload = {
            "password": data.get("user_password"),
            "email": data.get("email"),
            "mobile_number": data.get("phone"),
            "token_auth": token_auth,
            "token_type": mfa_provider,
            "ftm_act_method": "email"
        }
        headers = cls._get_fac_auth_header(
            data.get('admin_user'), data.get('admin_password')
        )
        api_url = cls._get_fac_api_url(data.get("ip"), "localusers")
        for i in range(capacity):
            username = f"{data.get('user_prefix')}{i}"
            payload["username"] = username
            err = cls._check_and_delete_user(api_url, headers, username)
            if err:
                failed_user.append(username)
                continue
            resp = requests.post(
                api_url, json=payload, headers=headers, verify=False
            )
            if resp.status_code < 400:
                user_info = resp.json()
                user_id = user_info.get('id')
                username = f"<LOCAL>{username}<{user_id}>"
                created_user.append(username)
            else:
                failed_user.append(username)
        return created_user, failed_user

    def prepare(self, data):
        users, failed_users = self.create_user(data)
        users_data, mfa_failed = self.register_mfa(users, data)
        return users_data, failed_users + mfa_failed

    @classmethod
    def delete_user(cls, data):
        failed = []
        headers = cls._get_fac_auth_header(
            data.get('admin_user'), data.get('admin_password')
        )
        api_url = cls._get_fac_api_url(data.get("ip"), "localusers")
        capacity = data.get("capacity")
        for i in range(capacity):
            username = f"{data.get('user_prefix')}{i}"
            err = cls._check_and_delete_user(api_url, headers, username)
            if err:
                failed.append(username)
        if failed:
            return f"Failed to delete users: {failed}"
        return "SUCCESS"

    def clean(self, data):
        return self.delete_user(data)

    def recycle(self, data):
        pass
