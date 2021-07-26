import os

from utils.logger import get_logger
from utils.ssh import SshInteractiveConnection

logger = get_logger()


def read_cert(folder_path, file_name, fgt_ip=None):
    file_path = os.path.join(folder_path, fgt_ip, file_name)
    try:
        logger.info(f"Loading Cert: {file_path}")
        with open(file_path) as f:
            return f.read()
    except Exception as err:
        logger.error(f"Failed to find cert: {file_path}")
        raise err


def send_commands(fgt_ip, cmd, fgt_config):
    ssh_client = SshInteractiveConnection(
        fgt_ip, fgt_config.get("user"), fgt_config.get("password")
    )
    output = ssh_client.send_commands(cmd)
    if SshInteractiveConnection.is_in_output("fail", output):
        logger.error("setup failed once")
        raise Exception("Setup is terminated by command fail. "
                        "Please check log Trackback")
    return output


def rename_fortigate(fgt_ip, hostname, fgt_config):
    cmd = [
        "config global",
        "config system global",
        f"set hostname {hostname}",
        "end",
        "end"
    ]
    send_commands(fgt_ip, cmd, fgt_config)


def upload_certificate_files(fgt_ip, folder_path, fgt_config):
    private_key = read_cert(folder_path, f"{fgt_ip}.key.pem", fgt_ip=fgt_ip)
    certificate_key = read_cert(folder_path, f"{fgt_ip}.cert.pem", fgt_ip=fgt_ip)
    ca1_key = read_cert(folder_path, "ca-chain1.cert.pem", fgt_ip=fgt_ip)
    ca2_key = read_cert(folder_path, "ca-chain2.cert.pem", fgt_ip=fgt_ip)
    upload_certi_cmd = [
        "config global",
        "config certificate local",
        f"edit {fgt_ip}.cert",
        "set password fortinet",
        f"set private-key '{private_key}'",
        f"set certificate '{certificate_key}'",
        "end",
        "end",
        "config global",
        "config certificate ca",
        "edit G_CA_Cert_1",
        f"set ca '{ca1_key}'",
        "next",
        "edit G_CA_Cert_2",
        f"set ca '{ca2_key}'",
        "end",
        "end"
    ]
    send_commands(fgt_ip, upload_certi_cmd, fgt_config)


def open_port2_to_ping_check(fgt_ip, fgt_config):
    last_ip_digit = fgt_ip.split('.')[-1]
    cmd = [
        "config global",
        "config system interface",
        "edit port2",
        "set allowaccess ping",
        f"set ip 192.168.0.{last_ip_digit} 255.255.255.0",
        "end",
        "end"
    ]
    send_commands(fgt_ip, cmd, fgt_config)


def setup_user_group(fgt_ip, fgt_config):
    cmd = [
        "config vdom",
        "edit root",
        "config user group",
        "edit ssl_vpn_group",
        "end",
        "end"
    ]
    send_commands(fgt_ip, cmd, fgt_config)


def set_firewall_policy(fgt_ip, fgt_config):
    common_cmd = [
        "set srcintf ssl.root",
        "set srcaddr all",
        "set dstaddr all",
        "set action accept",
        "set service ALL",
        "set groups ssl_vpn_group",
        "set schedule always",
        "set nat enable"
    ]
    ssl_vpn_cmd = [
                      "config vdom",
                      "edit root",
                      "config firewall policy",
                      "edit 2",
                      "set name ssl-vpn",
                      "set dstintf port1"
                  ] + common_cmd
    ping_check_cmd = [
                         "next",
                         "edit 3",
                         "set name ping-check",
                         "set dstintf port2"
                     ] + common_cmd
    cmd = ssl_vpn_cmd + ping_check_cmd + ["end", "end"]
    send_commands(fgt_ip, cmd, fgt_config)


def setup_ad_ldap_server(fgt_ip, fgt_info):
    ldap_info = fgt_info.get("ldap", {})
    ldap_user = ldap_info.get('user')
    ldap_server = ldap_info.get('server')
    ldap_cnid = ldap_info.get('cnid')
    ldap_dn = ldap_info.get('dn')
    ldap_username = ldap_info.get('username')
    ldap_passwd = ldap_info.get('password')
    cmd = [
        "config vdom",
        "edit root",
        "config user ldap",
        f"edit {ldap_user}",
        f"set server {ldap_server}",
        f"set cnid {ldap_cnid}",
        "set type regular",
        "set port 389",
        f"set dn {ldap_dn}",
        f"set username {ldap_username}",
        f"set password {ldap_passwd}",
        "end",
        "end"
    ]
    send_commands(fgt_ip, cmd, fgt_info)


def setup_radius_server(fgt_ip, radius_ip, fgt_info):
    cmd = [
        "config vdom",
        "edit root",
        "config user radius",
        f"edit {radius_ip}-radius",
        f"set server {radius_ip}",
        "set secret fortinet",
        "end",
        "end"
    ]
    send_commands(fgt_ip, cmd, fgt_info)


def change_firewall_address(fgt_ip, fgt_info):
    cmd = [
        "config vdom",
        "edit root",
        "config firewall address",
        "edit SSLVPN_TUNNEL_ADDR1",
        "set start-ip 192.168.0.200",
        "set end-ip 192.168.0.254",
        "end",
        "end"
    ]
    send_commands(fgt_ip, cmd, fgt_info)


def setup_ssl_vpn(fgt_ip, fgt_info):
    cmd = [
        "config vdom",
        "edit root",
        "config vpn ssl settings",
        f"set servercert {fgt_ip}.cert",
        "set idle-timeout 30",
        "set tunnel-ip-pools SSLVPN_TUNNEL_ADDR1",
        "set tunnel-ipv6-pools SSLVPN_TUNNEL_IPv6_ADDR1",
        "set source-interface port1",
        "set port 10443",
        "set source-address all",
        "set source-address6 all",
        "set login-attempt-limit 0",
        "set login-block-time 0",
        "set default-portal full-access",
        "end",
        "end"
    ]
    send_commands(fgt_ip, cmd, fgt_info)


def set_tunnel_mode_enable(fgt_ip, fgt_info):
    cmd = [
        "config vdom",
        "edit root",
        "config vpn ssl web portal",
        "edit full-access",
        "set tunnel-mode enable",
        "end",
        "end"
    ]
    send_commands(fgt_ip, cmd, fgt_info)


def setup_config(fgt_ip, radius_ip, hostname, config_info):
    logger.info(f"Start setup FGT at ip: {fgt_ip} now: ")
    folder_path = config_info.get("spec").get("data").get("sslcert").get("folder_path")
    fgt_info = config_info.get("spec").get("data").get("fgt", {})
    try:
        rename_fortigate(fgt_ip, hostname, fgt_info)
        upload_certificate_files(fgt_ip, folder_path, fgt_info)
        open_port2_to_ping_check(fgt_ip, fgt_info)
        setup_user_group(fgt_ip, fgt_info)
        setup_ssl_vpn(fgt_ip, fgt_info)
        set_firewall_policy(fgt_ip, fgt_info)
        setup_ad_ldap_server(fgt_ip, fgt_info)
        setup_radius_server(fgt_ip, radius_ip, fgt_info)
        change_firewall_address(fgt_ip, fgt_info)
        set_tunnel_mode_enable(fgt_ip, fgt_info)
        logger.info(f"Complete setup FGT at ip: {fgt_ip} now.")
        return "SUCCESS"
    except Exception as err:
        logger.exception(err)
        raise err
