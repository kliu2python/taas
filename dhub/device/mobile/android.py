import os
import shutil

import utils.android as android_lib
from dhub.device.base import Device


class AndroidDevice(Device):
    """
    Android device class for generate new emulator and others. for now only
    emulator supported
    """
    def __init__(self, config: dict, device_slot_id: int):
        self.device_slot_id = device_slot_id
        self.config = config
        self.device_name = self._generate_device_name()
        self.device_name = self._create_emulator_from_template()

    def _generate_device_name(self):
        return f"{self.config.get('platform_id')}_{self.device_slot_id}"

    @staticmethod
    def _check_emulator_file(*paths):
        if not sum([os.path.exists(path) for path in paths]) == len(paths):
            for path in paths:
                if os.path.isfile(path):
                    os.remove(path)
                if os.path.isdir(path):
                    shutil.rmtree(path)

    def _create_emulator_from_template(self):
        template = self.config.get("template_path")
        clear_user_data = self.config.get("clear_user_data")
        target_avd_folder = os.path.join(
            os.path.dirname(template),
            f"{self.device_name}.avd"
        )
        target_avd_ini = android_lib.get_ini_file_by_folder_name(
            target_avd_folder
        )
        source_avd_ini = android_lib.get_ini_file_by_folder_name(template)
        self._check_emulator_file(target_avd_folder, target_avd_ini)
        if os.path.exists(target_avd_ini):
            print("target avd exists, re-using existing ones")
            if clear_user_data:
                android_lib.kill_emulator(self.device_name)
                android_lib.clean_emulator_android_user_data(target_avd_folder)
        elif os.path.exists(template):
            shutil.copytree(template, target_avd_folder)
            shutil.copy(source_avd_ini, target_avd_ini)
        else:
            raise FileNotFoundError(f"Can not find template {template}")
        android_lib.update_avd_config_file(target_avd_folder)
        return self.device_name

    def get_device(self):
        return self.device_name

    def prepare_device(self, **kwargs):
        apk_file_path = kwargs.get("apk_file_path")
        if apk_file_path:
            android_lib.launch_emulator(self.device_name)
            android_lib.install_apk(self.device_name, apk_file_path)

    def clean_device(self):
        android_lib.kill_emulator(self.device_name)

    def op_run_adb_shell_cmd(self, adb_shell_cmds):
        return android_lib.run_adb_shell_commands(
            self.device_name, adb_shell_cmds
        )
