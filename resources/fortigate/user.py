import requests

from resources.ftc.user import User as FtcUser
from resources.pool import ResourcePoolMixin
from utils.logger import get_logger
from utils.ssh import SshInteractiveConnection

logger = get_logger()


class User(FtcUser, ResourcePoolMixin):
    @classmethod
    def create_user(cls, data):
        created_user = []
        failed_user = []
        capacity = data.get("capacity")
        ssh_client = SshInteractiveConnection(
            data.get("ip"), data.get("admin_user"), data.get("admin_password")
        )
        group = data.get("group")
        vdom = data.get("vdom", "root")
        vdom_cmd = [
            "config vdom",
            f"edit {vdom}"
        ]
        mfa_provider = data.get("mfa_provider")
        ssh_client.send_commands(vdom_cmd)
        cls._delete_membership(group, ssh_client)
        for i in range(capacity):
            user_name = f"{data.get('user_prefix')}{i}"
            password = data.get("user_password")
            commands = [
                "config user local",
                f"delete {user_name}",
                "end"
            ]
            ssh_client.send_commands(commands)
            commands = [
                "config user local",
                f"edit {user_name}"
            ]
            if not data.get("remote"):
                commands += [
                    "set type password",
                    f"set passwd {password}"
                ]
            else:
                commands += [
                    "set type radius",
                    "set radius-server radius"
                ]
            cell = data.get("cell")
            if cell:
                commands.append(f"set sms-phone {cell}")
            commands += [
                f"set email-to {data.get('email')}"
            ]
            if mfa_provider:
                commands += [
                    f"set two-factor {mfa_provider}"
                ]
            commands += [
                "end",
                "config user group",
                f"edit {group}",
                f"append member {user_name}",
                "end"
            ]
            out = ssh_client.send_commands(commands)
            no_error = True
            for line in out:
                if "Command fail" in line:
                    failed_user.append(user_name)
                    no_error = False
                    break
            if no_error:
                created_user.append(user_name)
        ssh_client.quit()
        return created_user, failed_user

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

    def prepare(self, data):
        users, failed_users = self.create_user(data)
        users_data, mfa_failed = self.register_mfa(users, data)
        return users_data, failed_users + mfa_failed

    @classmethod
    def delete_user(cls, data):
        deleted = []
        capacity = data.get("capacity")
        ssh_client = SshInteractiveConnection(
            data.get("ip"), data.get("admin_user"), data.get("admin_password")
        )
        vdom = data.get("vdom", "root")
        vdom_cmd = [
            "config vdom",
            f"edit {vdom}"
        ]
        ssh_client.send_commands(vdom_cmd)
        cls._delete_membership(data.get("group"), ssh_client)
        for i in range(capacity):
            user_name = f"{data.get('user_prefix')}{i}"
            command = [
                "config user local",
                f"delete {user_name}",
                "end"
            ]
            ssh_client.send_commands(command)
            deleted.append(user_name)
        ssh_client.quit()
        return "SUCCESS"

    def clean(self, data):
        return self.delete_user(data)

    def recycle(self, data):
        pass
