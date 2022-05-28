from time import sleep

import openstack

import selenium.webdriver.support.expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait

from openstack_api_client import OpenstackApiClient

INTERNAL_NET_NAME = "fis-internal"
FIS_USERNAME = "admin"
FIS_PASSWORD = ""
FIS_VIP = "10.0.0.254"
FIS_INTERNAL_GATEWAY = "10.0.0.1"
FIS_MGMT_GATEWAY = "10.2.0.1"
SERVER_PREFIX = "fis-cluster"
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

STACK_NAME = "stack1"
conn = openstack.connect(STACK_NAME)
network = conn.get_network(INTERNAL_NET_NAME)
server_ids = set()
openstack_api_client = OpenstackApiClient("stack1")
network_base_url = "http://10.160.83.5:9696/v2.0"
compute_base_url = "http://10.160.83.5:8774/v2.1"

XPATH = "/html/body/div[2]/canvas"


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
    ele = driver.find_element_by_xpath(XPATH) #find_element(driver)
    sleep(5)
    if ele:
        for cmd in cmds:
            ele.send_keys(f"{cmd}\n")
            sleep(1)
    else:
        print("Error: Selenium driver can not find console element")


def get_cmds(server):
    cmds = [FIS_USERNAME, FIS_PASSWORD]
    added = []
    for net_type, addr_list in server.addresses.items():
        if addr_list and net_type not in added:
            ip = addr_list[0]["addr"]
            port = PORT_NAME_MAPING.get(net_type)
            if port:
                net_mask = NET_MASK.get(port)
                cmds.append(f"set {port} {ip}/{net_mask}")

    cmds.extend(
        [
            f"set internal-gw 0.0.0.0/0 {FIS_INTERNAL_GATEWAY}",
            # f"set mgmt-gw 0.0.0.0/0 {FIS_MGMT_GATEWAY}",
            f"set dns 8.8.8.8 208.91.112.53",
            "set ha-enabled 1",
            f"set ha-virtual-ip {FIS_VIP}",
            f"set ha-priority 18",
            f"set ha-group-id 11",
            f"set ha-password abc123",
            f"set ha-group-ip 239.0.0.1",
            "set ha-group-port 5001",
            "set ha-interface mgmt",
            "exit"
        ]
    )
    return cmds


def reboot_server(server):
    conn.compute.reboot_server(server["id"], "HARD")


def config_fis_ip_ha(server):
    cmds = get_cmds(server)
    console_url = create_server_console(server["id"])
    driver = get_selenium_driver()
    driver.get(console_url)
    send_commands(driver, cmds)
    driver.close()
    reboot_server(server)


def setup_fis():
    for port in conn.list_ports(filters={"network_id": network["id"]}):
        server = conn.get_server(port["device_id"])
        if server and SERVER_PREFIX in server.get("name"):
            server_name = server["name"]
            print(f"Found FIS Server {server_name}")

            config_allowed_address_pairs(port, server_name)
            config_fis_ip_ha(server)
            break


if __name__ == "__main__":
    setup_fis()
