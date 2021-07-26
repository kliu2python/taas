# pylint: disable=too-many-arguments, unused-argument, unused-variable
from time import sleep

from utils.ssh import SshInteractiveConnection
from utils.logger import get_logger

logger = get_logger()


class SshCollector(SshInteractiveConnection):
    def __init__(
            self,
            ssh_user=None,
            ssh_password=None,
            ssh_ip=None,
            timeout=30,
            display=False,
            prepare_commands=None,
            expect_format=None,
            **data
    ):

        self.ssh_ip = ssh_ip
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.display = display
        self.exp_format = expect_format
        self.timeout = timeout
        if prepare_commands:
            self.prepare_commands = prepare_commands
        else:
            self.prepare_commands = []
        try:
            SshInteractiveConnection.__init__(
                self,
                self.ssh_ip,
                self.ssh_user,
                self.ssh_password,
                timeout=self.timeout,
                display=self.display
            )
            self.connected = True
        except Exception as e:
            logger.exception(
                f"Error when setup SSH connection to {self.ssh_ip}",
                exc_info=e
            )
            self.connected = False

    @staticmethod
    def get_status_dict(result):
        result_list = []
        result_dict = {}
        for i in result:
            result_list += i.split('\n')
        for i in result_list:
            temp_list = i.split(':')
            if len(temp_list) == 2:
                result_dict[temp_list[0].strip()] = temp_list[1].strip()
        return result_dict

    def get_active_session_count(self):
        commands = ['status']
        result = self.send_commands(commands, exp='.*>.*', display=self.display)
        result_dict = self.get_status_dict(result)
        return result_dict['Active Sessions']

    @staticmethod
    def calc_cpu_usage(result):
        result_list = []
        total, total_idle, non_idle = None, None, None
        for i in result:
            result_list += i.split('\n')
        for i in result_list:
            temp_list = i.split()
            if len(temp_list) > 0 and temp_list[0].strip() == 'cpu':
                (user, nice, system, idle, iowait, irq,
                 softirq, steal, guest, guest_nic) = [
                    float(x.strip()) for x in temp_list[1:]
                ]
                total_idle = idle + iowait
                non_idle = user + nice + system + irq + softirq + steal
                total = total_idle + non_idle
        return total_idle, non_idle, total

    @staticmethod
    def calc_cpu_percentage(
            total_idle,
            non_idle,
            total,
            prev_total_idle,
            prev_non_idle,
            prev_total
    ):
        return (
                100 * (
                    ((total - prev_total) - (total_idle - prev_total_idle))
                    / (total - prev_total)
                )
            )

    def get_cpu_usage(self):
        self.send_commands(
            self.prepare_commands, exp=self.exp_format, display=self.display
        )
        commands = ['cat /proc/stat']
        result = self.send_commands(
            commands, exp=self.exp_format, display=self.display
        )
        sleep(0.5)
        new_result = self.send_commands(
            commands, exp=self.exp_format, display=self.display
        )
        total_idle, non_idle, total = self.calc_cpu_usage(new_result)
        prev_total_idle, prev_non_idle, prev_total = self.calc_cpu_usage(result)
        percentage = self.calc_cpu_percentage(
            total_idle,
            non_idle,
            total,
            prev_total_idle,
            prev_non_idle,
            prev_total
        )
        return percentage

    @staticmethod
    def remove_kb(mem_str):
        temp_list = mem_str.strip().split()
        return float(temp_list[0])

    def get_memory_usage(self):
        commands = self.prepare_commands + ['cat /proc/meminfo']
        result = self.send_commands(
            commands, exp=self.exp_format, display=self.display
        )
        result_dict = self.get_status_dict(result)
        mem_total = self.remove_kb(result_dict['MemTotal'])
        mem_free = self.remove_kb(result_dict['MemAvailable'])
        return 100 * (mem_total - mem_free) / mem_total
