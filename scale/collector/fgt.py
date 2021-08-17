# pylint: disable=too-many-arguments,duplicate-code
import datetime
import difflib
import hashlib

from scale.db.logs import Command
from utils.ssh import SshNoneInteractiveConnection

CRASHLOG_CMD = [
    "config global",
    "diag debug crashlog read"
]


class FgtCollector(SshNoneInteractiveConnection):
    def __init__(self, session_id, data, crashlog_store=None):
        self.ssh_ip = data.get("ssh_ip")
        SshNoneInteractiveConnection.__init__(
            self,
            self.ssh_ip,
            data.get("ssh_user"),
            data.get("ssh_password")
        )
        self._last_cmdout_hash = None
        self._log_store = crashlog_store
        self.session_id = session_id
        self.category = data.get("category")
        self.remove_dup = data.get("remove_dup", False)
        if self.category in ["crashlog"]:
            self.commands = CRASHLOG_CMD
        else:
            self.commands = data.get("commands", [])
        self.session_query = f"{session_id}_fgt_{self.category}"

    def get_command_output(self):
        output = self.send_commands(self.commands)
        self.send_command("end")
        return output

    def refresh_command_output(self):
        output = self.get_command_output()
        if output:
            log_to_save = None
            if self.remove_dup:
                crashlog_hash = hashlib.md5(output.encode("utf-8")).hexdigest()
                if crashlog_hash != self._last_cmdout_hash:
                    if self._last_cmdout_hash:
                        self._log_store.incr(
                            "total_commands", 1, self.session_query
                        )
                    self._last_cmdout_hash = crashlog_hash
                    last_crashlog = self._log_store.get(
                        "last_command_log", self.session_query, default=""
                    )
                    diff = list(
                        difflib.unified_diff(
                            last_crashlog.split("\n"), output.split("\n")
                        )
                    )
                    crashlog_diff = ""
                    for d in diff[3:]:
                        if d.startswith("+"):
                            crashlog_diff += d[1:] + "\n"
                    log_to_save = crashlog_diff
            else:
                log_to_save = output
            self._log_store.set(
                "last_command_log", output, self.session_query
            )
            if log_to_save:
                log_to_save = (
                    f"*****{datetime.datetime.now()}*****\n{log_to_save}"
                )
                Command.write(self.session_id, self.category, log_to_save)
                if self._log_store:
                    self._log_store.set(
                        "command_log", [log_to_save], self.session_query
                    )

    def get_total_commands(self):
        self.refresh_command_output()
        value = self._log_store.get("total_commands", self.session_query)
        if not value:
            value = 0
        return [{
            "labels": {
                "device": "fgt",
                "ip": self.ssh_ip
            },
            "value": value
        }]
