import platform
import subprocess


def ping(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '2', host]
    try:
        output = subprocess.check_output(command).decode()
    except Exception as e:
        output = f"{e}"
    print(output)
    return "Approximate round trip times" in output


def ping_check(ip):
    result = False
    for _ in range(3):
        if ping(ip):
            result = True
            break
    return "pass" if result else "fail"
