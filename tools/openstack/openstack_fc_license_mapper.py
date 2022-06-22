import openstack
import yaml

from extract_registration_code import extract_license_code

MGMT_NET = "fis-mgmt"

SERVER_NAME = "fis-cluster"
LICENSE_PDF_FOLDER = r"C:\Users\znie\Documents\licenses_FG\LIC-FIS-VM_52593930"
NEW_SETUP = False
STACK_NAME = "stack1"
conn = openstack.connect(STACK_NAME)

if NEW_SETUP:
    reg_codes = list(extract_license_code(LICENSE_PDF_FOLDER).keys())
    ip_reg_mapping = {}
else:
    with open("register_code_mapping.yaml") as F:
        reg = yaml.safe_load(F)
        reg_codes = reg["unused"]
        ip_reg_mapping = reg["assigned"]

servers = conn.list_servers(filters={"name": SERVER_NAME})

for server in servers:
    ip = server["addresses"][MGMT_NET][0]["addr"]
    if ip not in ip_reg_mapping:
        ip_reg_mapping[ip] = {"reg_code": reg_codes.pop(0)}

to_file = {
    "assigned": ip_reg_mapping,
    "unused": reg_codes
}

with open("register_code_mapping.yaml", "w") as F:
    yaml.safe_dump(to_file, F)
