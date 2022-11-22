import re
import socket
from time import sleep

from paramiko.buffered_pipe import PipeTimeout

from upgrade.constants import PRODUCT_MAPPING
from utils.logger import get_logger
from utils.ssh import CommandFailedError
from utils.ssh import CommandParseError
from utils.ssh import CommandUnknownActionError
from utils.ssh import SshInteractiveConnection

logger = get_logger("clear")


class FgtSsh(SshInteractiveConnection):
    def __init__(
            self,
            host,
            username,
            password,
            timeout=30,
            has_vdom=None
    ):
        super().__init__(host, username, password, timeout)
        self.has_vdom = has_vdom

    def reboot_system(self):
        cmd = [
            "exec reboot",
            "y"
        ]
        self.send_commands(cmd, ignore_timeout=True, display=False)

    # pylint: disable=arguments-differ,raise-missing-from
    def send_commands(
            self,
            commands: list,
            exp=None,
            display=True,
            timeout=None,
            new_line=True,
            ignore_timeout=True,
            retry=3,
            ignore_error=False
    ):
        output = None
        while retry > 0:
            try:
                self.back_to_root_level()
                output = super().send_commands(
                    commands,
                    exp=exp,
                    display=display,
                    timeout=timeout,
                    new_line=True
                )
                break
            except Exception as e:
                if display:
                    logger.exception("retry commands due to error", exc_info=e)
                ex = e
                try:
                    self.quit()
                    self.connect()
                except Exception as e:
                    if display:
                        logger.exception(
                            "Error reconnect during retry cmd", exc_info=e
                        )

                retry -= 1
                if retry <= 0:
                    if isinstance(ex, (PipeTimeout, socket.timeout)):
                        if not ignore_timeout:
                            raise ex
                        logger.info(
                            "socket timeout, but we choose to ignore"
                        )
                    else:
                        if not ignore_error:
                            raise ex
                        logger.info(
                            f"We have exception, now ignore: {ex}"
                        )
                sleep(3)
        return output

    def back_to_root_level(self):
        super().send_commands(
            ["end"] * 5,
            display=False,
            ignore_error=True
        )

    def has_global(self):
        if self.has_vdom is None:
            retry = 5
            while retry:
                try:
                    self.back_to_root_level()
                    self.send_commands(
                        ["config global"], retry=1, display=False
                    )
                    logger.info("System multivdom is enabled")
                    self.has_vdom = True
                    break
                except (
                        CommandParseError,
                        CommandUnknownActionError,
                        CommandFailedError
                ):
                    self.has_vdom = False
                    logger.info("System multivdom is disabled")
                    break
                except (socket.timeout, socket.error):
                    logger.info("Socket error, retrying")
                sleep(5)
            if self.has_vdom is None:
                raise LookupError("Can not determine multivdom")
            self.back_to_root_level()
        return self.has_vdom

    def backup_settings(self, file, tftp_ip):
        self.back_to_root_level()
        cmds = [
            f"execute backup config tftp {file} {tftp_ip}"
        ]
        if self.has_global():
            cmds = ["config global"] + cmds
        self.send_commands(cmds)

    def wait_fortigate_bootup(self):
        logger.info("Waiting Fortigate Bootup")
        retry = 30
        while retry > 0:
            try:
                sleep(30)
                self.quit()
                self.connect()
                logger.info("Fortigate is up!")
                break
            except Exception as e:
                logger.info(f"waiting FGT boot up({retry})")
                if retry == 1:
                    logger.info("Fortigate failed to boot")
                    raise e
            retry -= 1

    def restore_settings(self, file, tftp_ip):
        self.back_to_root_level()
        cmds = [
            f"execute restore config tftp {file} {tftp_ip}",
            "y"
        ]
        if self.has_global():
            cmds = ["config global"] + cmds
        self.send_commands(cmds, ignore_timeout=True, display=False)
        self.wait_fortigate_bootup()

    def restore_binary(self, file, file_type, ip, user, password):
        self.back_to_root_level()
        cmds = [
            f"execute restore {file_type} ftp {file} {ip} {user} {password}",
            "y",
            "y"
        ]
        if self.has_global():
            cmds = ["config global"] + cmds
        self.send_commands(cmds, ignore_timeout=True, display=True,
                           ignore_error=True, timeout=120, retry=1)
        if file_type in ["image"]:
            self.wait_fortigate_bootup()

    def get_model_version(self):
        try:
            self.back_to_root_level()
            cmd = [
                "get system status"
            ]
            out = self.send_commands(cmd, display=False)
            if out:
                out = out[-1].split("\n")
                for line in out:
                    if line.startswith("Version:"):
                        model = line.split()[1]
                        model_list = model.split("-")
                        prod = model_list[0].lower()
                        prod = PRODUCT_MAPPING.get(prod)
                        if prod:
                            model_list[0] = prod.upper()
                            model = "_".join(model_list)
                            return model, line
            else:
                raise Exception("Failed to execute get system status command")
        except Exception as e:
            logger.exception("Error when get system status", exc_info=e)
            raise e

    def get_device_info(self, repo=None):
        model, _ = self.get_model_version()
        model_num = int(model.split("_")[1][:-1])
        if model_num >= 6000:
            if not repo:
                repo = "FortiOS-6K7K"
            if model_num < 7000:
                model = f"6000{model[-1]}"
            elif model_num >= 7000:
                model = f"7000{model[-1]}"
        image_name = fr"{model}-(.*).out$"
        return repo, image_name


if __name__ == "__main__":
    FgtSsh("10.160.88.29", "admin", "admin", False)
