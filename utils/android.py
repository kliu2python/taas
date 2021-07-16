import os
import re
import shutil
import time

from typing import List, Tuple, Any, Union, Dict
from pathlib import Path
from subprocess import check_output
from telnetlib import Telnet


to_delete = [
    "userdata-qemu.img",
    "snapshots"
]
android_home = os.environ.get("ANDROID_HOME")
ADB_PATH = "adb"
EMULATOR_EXE_PATH = "emulator"
if android_home:
    ADB_PATH = os.path.join(android_home, "platform-tools", ADB_PATH)
    EMULATOR_EXE_PATH = os.path.join(
        android_home, "emulator", EMULATOR_EXE_PATH
    )


def update_ini_file(file: str, dict_to_update: dict):
    if os.path.exists(file):
        with open(file, "r") as FILE:
            lines = FILE.readlines()
        with open(file, "w") as FILE:
            lines_to_write = []
            for line in lines:
                for k, v in dict_to_update.items():
                    if f"{k}" in line:
                        line_eque = " = " if " = " in line else "="
                        line = f"{k}{line_eque}{v}\n"
                        break
                lines_to_write.append(line)
            FILE.writelines(lines_to_write)
    else:
        print(f"ini file: {file} does not exist!!!")


def get_ini_file_by_folder_name(avd_path):
    ini_file = os.path.join(
        os.path.dirname(avd_path),
        f"{Path(avd_path).stem}.ini"
    )
    return ini_file


def update_avd_config_file(avd_folder):
    ini_file = get_ini_file_by_folder_name(avd_folder)
    avd_config_to_update = {
        "path": avd_folder,
        "path.rel": os.path.join(
            os.path.basename(os.path.dirname(avd_folder)),
            os.path.basename(avd_folder)
        )
    }
    update_ini_file(ini_file, avd_config_to_update)

    avd_name = Path(avd_folder).stem
    avd_config_to_update = {
        "AvdId": avd_name,
        "avd.ini.displayname": avd_name
    }
    update_ini_file(
        os.path.join(avd_folder, "config.ini"),
        avd_config_to_update
    )

    avd_config_to_update = {
        "avd.name": avd_name,
        "avd.id": avd_name,
        "disk.cachePartition.path": os.path.join(avd_folder, "cache.img"),
        "disk.dataPartition.path": os.path.join(
            avd_folder, "userdata-qemu.img"
        ),
        "disk.encryptionKeyPartition.path": os.path.join(
            avd_folder, "encryptionkey.img"
        )
    }
    update_ini_file(
        os.path.join(avd_folder, "hardware-qemu.ini"),
        avd_config_to_update
    )


def clean_emulator_android_user_data(avd_folder_path):
    for target in to_delete:
        file_path = os.path.join(avd_folder_path, target)
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=True)


def get_all_adb_devices():
    adb_out = (
        check_output([ADB_PATH, "devices"]).decode().rstrip(
            '\r\n').split("\n")
    )
    ret = []
    if isinstance(adb_out, list):
        if len(adb_out) > 1:
            for line in adb_out[1:]:
                if line:
                    device = re.match(r"(.*?)\t", line).group(1)
                    ret.append(device)
    return ret


def get_all_emulator_ports():
    adb_devices = get_all_adb_devices()
    ret = {}
    if adb_devices:
        for device in adb_devices:
            if "emulator" in device:
                ret[device] = device.split('-')[-1]
    return ret


def get_avd_name_from_port():
    ret = {}
    ports = get_all_emulator_ports()
    for emu_name, port in ports.items():
        try:
            telnet = Telnet("localhost", port, timeout=30)
            name = ""
            timeout = 10
            while timeout > 0:
                telnet.write(b"avd name\r\n")
                name = telnet.read_very_eager().decode()
                if name.count("\r\nOK\r\n") > 0:
                    break

                time.sleep(0.1)
                timeout -= 0.1
            else:
                print("Time out when try to wait for information")
            name = re.search(
                r"(?<=\r\nOK\r\n)(.*)(?=\r\nOK\r\n)", name
            ).group(0)
            ret[name] = emu_name
            telnet.close()
        except Exception as e:
            print(f"Error when try to find avd name for {emu_name}"
                  f"error: {e}")
    return ret


def kill_emulator(avd_name):
    emu_name = get_avd_name_from_port().get(avd_name)
    if emu_name is not None:
        cmd = f"{ADB_PATH} -s {emu_name} emu kill".split()
        out = check_output(cmd, timeout=10).decode()
        if "bye" in out and "\r\r\nOK\r\r\n" in out:
            timeout = 5
            while timeout > 0:
                if emu_name in get_all_adb_devices():
                    time.sleep(1)
                    timeout -= 1
                else:
                    break
            else:
                print("Time out when try to wait for emulator to kill")
    else:
        print(f"avd {avd_name} is not running")


def launch_emulator(emulator_name: str, *args):
    cmd = f"{EMULATOR_EXE_PATH} -avd {emulator_name} {' '.join(args)} &"
    check_output(cmd, timeout=10)
    retry = 5
    while retry > 0:
        running_avd_names = get_avd_name_from_port()
        if emulator_name in running_avd_names:
            break
        retry -= 1
        time.sleep(1)


def install_apk(device_name: str, apk_file_path: str):
    """
    install a apk file for android devices
    :param device_name: device name assigned, not adb device name
    :param apk_file_path: apk files to install
    :return:
    """
    emu_name = get_avd_name_from_port().get(device_name)
    if emu_name is not None:
        cmd = f"{ADB_PATH} -s {emu_name} install -r {apk_file_path}"
        out = check_output(cmd, timeout=100).decode()
        if "Success" not in out:
            raise Exception(f"APK {apk_file_path} install Error!")


def run_adb_shell_commands(
        device_name: str, cmds: List[Dict]
) -> Union[List[Union[Tuple[Any, str], Tuple[str, str]]], str]:
    """
    Issue adb commands and check output.
    :param device_name: device name to check, not adb device name
    :param cmds: command list to issue with expected output, put to list [()]
    :return: str
    """
    def check_out(command, d_name, expected_output, su_mode=True):
        if su_mode:
            command = f"{ADB_PATH} -s {d_name} shell su 0 {command}"
        else:
            command = f"{ADB_PATH} -s {d_name} shell {command}"
        out_result = check_output(command, timeout=10, shell=True).decode()
        print(
            f"Issuing adb command: {command}"
            f"\n out: {out_result}"
            f"\n expected: {expected_output}"
        )
        if expected_output is not None and expected_output not in out_result:
            return f"Fail, {expected_output}", False
        return out_result, True

    emu_name = get_avd_name_from_port().get(device_name)
    if emu_name is not None:
        out_ret = []
        for cmd_dict in cmds:
            cmd = cmd_dict.get("cmd")
            expect_out = cmd_dict.get("expect_out")
            out, result = check_out(cmd, emu_name, expect_out, su_mode=True)
            out_ret.append((cmd, out))
            if result:
                continue
            out, result = check_out(cmd, emu_name, expect_out, su_mode=False)
            out_ret.append((f"su {cmd}", out))
        return out_ret
    return f"Error: device {device_name} is not started"
