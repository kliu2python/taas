from time import sleep

import yaml

from license_manager import LicenseManager

USERNAME = "ftc.manual.znie@gmail.com"
PASSWORD = "Fortinet_123"

manager = LicenseManager(USERNAME, PASSWORD)
manager.login()

with open("register_code_mapping.yaml") as F:
    reg_data = yaml.safe_load(F)

reg_codes = reg_data["assigned"]

for ip, data in reg_codes.items():
    retry = 3
    while retry > 0:
        try:
            print("Registering:", ip, data["reg_code"])
            sn = data.get("sn")
            if sn:
                print(ip, data["reg_code"], "already registered")
                break

            serial_number = manager.register_device(data["reg_code"], ip)
            reg_data["assigned"][ip]["sn"] = serial_number
            with open("register_code_mapping.yaml", "w") as F:
                yaml.safe_dump(reg_data, F)
            break
        except Exception as e:
            retry -= 1
            if retry <= 0:
                raise e

            print(
                "Error when register", e,
                "cooling down for 30 second and retry"
            )
            manager.close()
            sleep(30)

            manager.get_driver()
            manager.login()
