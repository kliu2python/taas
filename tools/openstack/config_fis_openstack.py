import os
from time import sleep

import openstack
import yaml

import selenium.webdriver.support.expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait

from openstack_api_client import OpenstackApiClient


# FIS Information
INTERNAL_NET_NAME = "fis-internal"
FIS_USERNAME = "admin"
FIS_PASSWORD = ""
FIS_VIP = "10.0.3.254"
FIS_INTERNAL_GATEWAY = "10.0.0.1"
FIS_HA_GATEWAY = "192.168.4.1"
FIS_HA_SUBNET = "192.168.4.0/22"
FIS_MGMT_GATEWAY = "10.2.0.1"
SERVER_PREFIX = "fis-cluster2"
TFTP_SERVER = "10.2.1.223"
EXCLUDE_SERVERS = ["fis-cluster-0", "fis-cluster-1", "fis-cluster-2"]
# [f"{SERVER_PREFIX}-{i}" for i in range(1, 251)]
PORT_NAME_MAPING = {
    "fis-mgmt": "mgmt-ip",
    "fis-internal": "internal-ip",
    "fis-ha": "ha-ip"
}
NET_MASK = {
    "mgmt-ip": 22,
    "internal-ip": 22,
    "ha-ip": 22
}
LICENSE_FOLDER = r"C:\Users\w10\Documents\fis_lics"

# Openstack Information
STACK_NAME = "stack1"
conn = openstack.connect(STACK_NAME)
network = conn.get_network(INTERNAL_NET_NAME)
server_ids = set()
openstack_api_client = OpenstackApiClient("stack1")
network_base_url = "http://10.160.83.5:9696/v2.0"
compute_base_url = "http://10.160.83.5:8774/v2.1"

XPATH = "/html/body/div[2]/canvas"
LIC_CONFIG = {}


def load_license_config():
    global LIC_CONFIG
    with open("register_code_mapping.yaml") as F:
        LIC_CONFIG = yaml.safe_load(F)["assigned"]


def update_allowed_port_pairs(port_id, ip_mac_pairs):
    allowed_pairs = []
    for ip_pair in ip_mac_pairs:
        ip = ip_pair[0]
        pair_dict = {
            "ip_address": ip
        }
        if len(ip_pair) == 2:
            mac = ip_pair[1]
            pair_dict["mac_address"] = mac
        allowed_pairs.append(pair_dict)
    param = {
        "port": {
            "allowed_address_pairs": allowed_pairs
        }
    }
    res = openstack_api_client.request(
        "PUT", f"{network_base_url}/ports/{port_id}", json=param
    )
    if res.status_code == 200:
        print(f"allowed address pair add success for {port_id}")
        return
    print(f"Failed to add pair, status code: {res.status_code}, {res.content}")


def create_server_console(server_id):
    param = {
        "remote_console": {
            "protocol": "vnc",
            "type": "novnc"
        }
    }
    res = openstack_api_client.request(
        "POST", f"{compute_base_url}/servers/{server_id}/remote-consoles",
        headers={"OpenStack-API-Version": "compute 2.6"},
        json=param
    )
    if res.status_code == 200:
        return res.json()["remote_console"]["url"]
    print("failed to get console url")


def config_allowed_address_pairs(port, server_name):
    pairs = port.get("allowed_address_pairs")
    need_pairs = True
    if pairs:
        for pair in pairs:
            if FIS_VIP in pair.get("ip_address"):
                need_pairs = False
                break
    if need_pairs:
        print(f"Adding allowed address pair for server {server_name}")
        update_allowed_port_pairs(port["id"], [[FIS_VIP]])
    else:
        print(f"Allowed pair already exists")


def get_selenium_driver():
    parm = {}
    cap = DesiredCapabilities.CHROME
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument('--ignore-certificate-errors')
    driver = webdriver.Chrome
    parm["desired_capabilities"] = cap
    parm["options"] = options

    return driver(**parm)


def find_element(driver):
    wait = WebDriverWait(driver, 10)
    return wait.until(
        ec.presence_of_element_located((By.XPATH, XPATH))
    )


def send_commands(driver, cmds):
    ele = driver.find_element_by_xpath(XPATH)
    sleep(5)
    if ele:
        for cmd in cmds:
            ele.send_keys(f"{cmd}\n")
            sleep(1)
    else:
        print("Error: Selenium driver can not find console element")


def get_lic_command(ip):
    sn = LIC_CONFIG[ip]["sn"]
    cmds = [f"update-license tftp {sn}.lic {TFTP_SERVER}", "y"]
    return cmds


def get_cmds(server, priority):
    cmds = [FIS_USERNAME, FIS_PASSWORD]
    added = []
    license_command = []
    for net_type, addr_list in server.addresses.items():
        if addr_list and net_type not in added:
            ip = addr_list[0]["addr"]
            port = PORT_NAME_MAPING.get(net_type)
            if port:
                net_mask = NET_MASK.get(port)
                cmds.append(f"set {port} {ip}/{net_mask}")
                if port == "mgmt-ip" and LICENSE_FOLDER:
                    license_command = get_lic_command(ip)

    cmds.extend(
        [
            f"set internal-gw 0.0.0.0/0 {FIS_INTERNAL_GATEWAY}",
            "set dns 8.8.8.8 208.91.112.53",
            "set ha-enabled 1",
            f"set ha-virtual-ip {FIS_VIP}",
            f"set ha-priority {priority}",
            "set ha-group-id 11",
            "set ha-password abc123",
            "set ha-group-ip 239.0.0.1",
            "set ha-group-port 5001",
            "set ha-interface ha",
            "reboot",
            "y",
            "y"
        ]
    )
    # cmds.extend(license_command)
    return cmds


def reboot_server(server):
    conn.compute.reboot_server(server["id"], "HARD")


def config_fis_ip_ha(server, ha_priority):
    cmds = get_cmds(server, ha_priority)
    console_url = create_server_console(server["id"])
    driver = get_selenium_driver()
    driver.get(console_url)
    send_commands(driver, cmds)
    driver.close()
    # reboot_server(server)


def setup_fis():
    load_license_config()

    for port in conn.list_ports(filters={"network_id": network["id"]}):
        server = conn.get_server(port["device_id"])
        if server and SERVER_PREFIX in server.get("name"):
            server_name = server["name"]
            print(f"Found FIS Server {server_name}")
            if server_name in EXCLUDE_SERVERS:
                print(f"Skipping Server {server_name}")
                continue

            priority = server_name.replace(SERVER_PREFIX + "-", "")
            print(f"HA priority: {priority}")
            config_allowed_address_pairs(port, server_name)
            config_fis_ip_ha(server, int(priority))
            print("----------------------------------")


if __name__ == "__main__":
    setup_fis()
