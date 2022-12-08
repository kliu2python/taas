import re
import socket

import paramiko
from paramiko_expect import SSHClientInteraction

from utils.logger import get_logger


class CommandParseError(Exception):
    pass


class CommandFailedError(Exception):
    pass


class CommandUnknownActionError(Exception):
    pass


class SshInteractiveConnection:
    def __init__(self, hostname, username, password, timeout=30, display=True):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.logger = get_logger(name=f"cli.{hostname}")
        self.timeout = timeout
        self.display = display
        self.disconnected = True
        self.con = None
        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        # Set SSH key parameters to auto accept unknown hosts
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(
            hostname=self.hostname,
            username=self.username,
            password=self.password
        )
        self.con = SSHClientInteraction(
            self.client,
            timeout=self.timeout,
            display=self.display,
            tty_height=1000
        )
        self.disconnected = False

    def clear_cache(self):
        self.con.current_output = ""

    def handle_promote_cmd(self, command):
        tailed_message = ""

        cmd_list = command.split("...")
        cmd = cmd_list[0]
        response = cmd_list[1]
        res = 0
        self.con.send(cmd + "\r")
        while res > -1:
            res = self.con.expect(
                r".*\(y\/n\)", output_callback=self.logger.info
            )
            tailed_message += self.con.current_output
            if res > -1:
                self.con.send(response)
        return tailed_message

    def send_command(
            self,
            command=None,
            exp=None,
            timeout=None,
            ignore_error=False
    ):
        if self.disconnected:
            self.connect()
        if timeout is None:
            timeout = self.timeout
        if not exp:
            exp = r".*\s#\s$"
        if command is not None:
            if "..." in command:
                curr_output = self.handle_promote_cmd(command)
            else:
                self.con.send(command + "\r")
                self.con.expect(
                    exp,
                    timeout=timeout,
                    output_callback=self.logger.info
                )
                curr_output = self.con.current_output
            if not ignore_error:
                if 'command parse error' in curr_output.lower():
                    raise CommandParseError()
                if "command fail" in curr_output.lower():
                    raise CommandFailedError()
                if "unknown action" in curr_output.lower():
                    raise CommandUnknownActionError()

            return curr_output

    def send_commands(
            self,
            commands: list,
            exp=None,
            timeout=None,
            ignore_error=False
    ):
        if isinstance(commands, str):
            commands = [commands]
        output = []
        for command in commands:
            out = self.send_command(
                command,
                exp,
                timeout=timeout,
                ignore_error=ignore_error
            )
            output.append(out)

        return output

    def quit(self):
        self.logger.info(self.con.current_output)
        self.con.close()
        self.client.close()
        self.disconnected = True
        self.clear_cache()

    @staticmethod
    def is_in_output(value, output):
        for line in output:
            if value in line:
                return True
        return False


class SshNoneInteractiveConnection:
    def __init__(self, host, username, password, timeout=2):
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout
        self.logger = get_logger(name=f"cli.{host}")
        self.client = None
        self.disconnected = True
        self.connect()

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname=self.host, username=self.username,
                            password=self.password)
        self.disconnected = False

    def _send_commands(self, cmds):
        channel = self.client.invoke_shell()
        channel.settimeout(self.timeout)
        for cmd in cmds:
            channel.send(f"{cmd}\n")

        buffer = ""
        run = True
        while run:
            try:
                data = channel.recv(4096)
                data = data.decode("utf-8")
                if data:
                    buffer += data
            except socket.timeout:
                run = False
        channel.close()
        return buffer

    def send_command(self, cmd):
        return self.send_commands([cmd])

    def quit(self):
        self.client.close()
        self.disconnected = False

    def send_commands(self, cmds, **kwargs):
        if kwargs:
            self.logger.debug(f"{kwargs} args will be ignored")
        retry = 5
        while retry > 0:
            try:
                return self._send_commands(cmds)
            except Exception as e:
                retry -= 1
                if retry <= 0:
                    raise e
                self.quit()
                self.connect()
