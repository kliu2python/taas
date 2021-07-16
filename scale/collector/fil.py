# pylint: disable=too-many-arguments,duplicate-code
from scale.collector.ssh import SshCollector


class FilCollector(SshCollector):
    def __init__(
            self,
            ssh_user,
            ssh_password,
            ssh_ip,
            timeout=30,
            display=False,
            **data
    ):
        SshCollector.__init__(
            self,
            ssh_user,
            ssh_password,
            ssh_ip,
            timeout,
            display,
            prepare_commands=data.get("prepare_commands", ['fnsysctl shell']),
            expect_format=data.get("expect_cmd_format", '.*[#>].*'),
            **data
        )
