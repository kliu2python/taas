# pylint: disable=too-many-arguments, duplicate-code
from scale.collector.ssh import SshCollector


class FtcCollector(SshCollector):
    def __init__(
            self,
            ssh_user,
            ssh_password,
            ssh_ip,
            target_server_ip=None,
            timeout=30,
            display=False,
            **data
    ):
        self.prepare_commands = data.get(
            "prepare_commands", [f"ssh centos@{target_server_ip}"]
        )
        self.exp_format = data.get("expect_cmd_format", '.*[$].*')
        self.display = display
        SshCollector.__init__(
            self,
            ssh_user,
            ssh_password,
            ssh_ip,
            timeout,
            display,
            prepare_commands=self.prepare_commands,
            expect_format=self.exp_format,
            **data
        )

    def get_active_session_count(self):
        return 0
