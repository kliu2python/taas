# pylint: disable=too-many-arguments,too-many-instance-attributes,
from time import sleep

import paramiko
from paramiko_expect import SSHClientInteraction

from utils.logger import get_logger
from utils.threads import thread

logger = get_logger()


class SSHConnection:
    def __init__(self, hostname, username, password, timeout=30, display=True):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout
        self.display = display
        self.disconnected = True
        self.skip_exp = None
        self.con = None
        self.client = None
        self.connect()

    def connect(self):
        self.client = paramiko.SSHClient()
        # Set SSH key parameters to auto accept unknown hosts
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname=self.hostname, username=self.username,
                            password=self.password)
        self.con = SSHClientInteraction(self.client, timeout=self.timeout,
                                        display=self.display, tty_height=1000,
                                        newline='')
        self.skip_exp = False
        self.disconnected = False

    def extract_output(self, exp, timeout=None):
        if not self.skip_exp:
            if exp is False:
                if timeout is None:
                    sleep(2)
                    exp = '.*'
                else:
                    sleep(timeout)
            elif exp is None:
                exp = r'.*\s#.*'

            self.con.expect(exp, timeout=timeout, default_match_prefix='.*')
        return self.con.current_output

    def send_command(self, command=None, exp: str = None, display=False,
                     new_line=True, timeout=None, exp_output=False):
        retry = 5
        while retry > 0:
            try:
                return self._send_command(
                    command, exp, display, new_line, timeout, exp_output
                )
            except Exception as e:
                retry -= 1
                if retry <= 0:
                    raise e
                sleep(2)
                self.quit()
                self.connect()

    def _send_command(self, command=None, exp: str = None, display=False,
                     new_line=True, timeout=None, exp_output=False):
        first_output = None

        if self.skip_exp:
            self.skip_exp = False
        else:
            self.extract_output(exp=exp, timeout=timeout)

        if command is not None:
            if new_line:
                command += '\r'
            self.con.send(command)

        if exp_output is not False:
            first_output = self.con.current_output
            self.extract_output(exp_output, timeout=timeout)
            self.skip_exp = True

        if display:
            print('PREVIOUSLY:')

            if exp_output is False:
                print(self.con.current_output)
            else:
                print(first_output)

            print(f'SENT: {command}')

            if exp_output is not False:
                print('CURRENT:')
                print(self.con.current_output)

        if 'command parse error' in self.con.current_output:
            raise Exception(self.con.current_output)

        return self.con.current_output

    def send_commands(self, commands: list, exp=None, display=True, timeout=30,
                      new_line=True):
        if isinstance(commands, str):
            commands = [commands]
        output = []
        for command in commands:
            output.append(self.send_command(command, exp, display=display,
                                            timeout=timeout))
        if new_line:
            output.append(
                self.send_command(' ', exp, display=display, timeout=timeout))

        for line in output:
            if 'Command fail' in line:
                print('Command failed')
                print(output)
            break
        if len(output) == 1:
            return output[0]
        return output

    @thread
    def send_commands_parallel(
            self, commands: list,
            exp=None,
            display=True,
            timeout=None,
            new_line=True
    ):
        return self.send_commands(
            commands, exp, display, timeout, new_line
        )

    def get_output(self):
        return self.con.current_output

    def quit(self):
        self.con.close()
        self.client.close()
        self.disconnected = True

    @staticmethod
    def is_in_output(value, output):
        for line in output:
            if value in line:
                return True
        return False
