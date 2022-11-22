import os
from time import sleep

import requests

import taascli.upgrade.templates as templates
from taascli.conf import CACHE_DIR
from taascli.utils import get_api_url
from taascli.utils import load_file
from taascli.utils import load_pickle
from taascli.utils import PrintInColor
from taascli.utils import save_pickle

CACHE_FILE = os.path.join(CACHE_DIR, "last_upgrades.pickle")


def update_sys(args):
    data = load_file(args)
    if not data:
        data = [{
            "platform": args.platform,
            "build_info": {
                "version": args.version,
                "product": args.product,
                "repo": args.repo,
                "branch": args.branch,
                "build": args.build,
                "type": args.type,
                "file_pattern": args.file_pattern
            },
            "device_access": {
                "host": args.ip,
                "username": args.username,
                "password": args.password
            }
        }]

    ret = []
    for d in data:
        resp = requests.post(
            get_api_url(f"upgrade/v1/update", 8006), json=d, verify=False
        )
        res = resp.json()
        PrintInColor.yellow(res)
        ret.append(res)
    if os.path.exists(CACHE_FILE):
        history = load_pickle(CACHE_FILE)
        if history and isinstance(history, list):
            ret = history + ret
    save_pickle(ret, CACHE_FILE)
    if args.wait:
        PrintInColor.yellow("Waiting upgrade finish. "
                            "press Ctrl + C to force exit, "
                            "upgrade process will not impact if force exit")
        _wait_upgrade_complete(ret)


def cancel_update(args):
    resp = requests.delete(
        get_api_url(f"upgrade/v1/update/{args.id}", 8006), verify=False
    )
    if resp.status_code == 200:
        PrintInColor.green("success")
    else:
        PrintInColor.red("fail")


def _get_upgrade_status(upgrade_id):
    resp = requests.get(
        get_api_url(f"upgrade/v1/update/{upgrade_id}", 8006), verify=False
    )
    return resp.json()


def _show_update_by_id(upgrade_id):
    out = _get_upgrade_status(upgrade_id)
    status = out.get("status")

    if status:
        if "fail" in status:
            PrintInColor.red(out)
        elif "completed" in status:
            PrintInColor.green(out)
        else:
            PrintInColor.yellow(out)
        return True
    else:
        PrintInColor.yellow(
            "Upgrade status has expired, "
            "upgrade status will be cleared every 48 hours, "
            "and will not show next time"
        )


def show_update(args):
    if args.id:
        _show_update_by_id(args.id)
    else:
        if os.path.exists(CACHE_FILE):
            data = load_pickle(CACHE_FILE)
            if args.wait:
                _wait_upgrade_complete(data)
            else:
                data_to_keep = []
                for d in data:
                    upgrade_id = d.get("upgrade_id")
                    if upgrade_id:
                        keep = _show_update_by_id(upgrade_id)
                        if keep:
                            data_to_keep.append(d)
                        save_pickle(data_to_keep, CACHE_FILE)
                    else:
                        PrintInColor.yellow(f"Missing upgrade id for {d}")
        else:
            PrintInColor.yellow("You have not have any last upgrade yet")


def _wait_upgrade_complete(upgrade_data):
    while upgrade_data:
        data = upgrade_data.pop(0)
        upgrade_id = data.get("upgrade_id")
        if upgrade_id:
            info = _get_upgrade_status(upgrade_id)
            status = info.get("status")
            if status and "completed" in status:
                PrintInColor.green(info)
                continue
            if status and "fail" in status:
                PrintInColor.red(info)
                continue
        else:
            PrintInColor.red(f"Can not find upgrade id for {data}")
            continue
        upgrade_data.append(data)
        sleep(3)


def generate_config(args):
    file = args.out
    file_dir = os.path.dirname(file)

    if os.path.exists(file_dir) or not file_dir:
        file_name = os.path.basename(file)
        if os.path.extsep in file_name:
            file_ext = os.path.splitext(file_name)[1].lower().strip()
        else:
            PrintInColor.red("Missing file extention."
                             " .yaml/.yml or .json needed")
            return

        if file_ext in [".yaml", ".yml"]:
            content = templates.CONFIG_TEMPLATES_YAML
        elif file_ext in [".json"]:
            content = templates.CONFIG_TEMPLATES_JSON
        else:
            PrintInColor.red(f"Invalied file extenstion {file_ext}, "
                             f".yaml/.yml or .json supported")
            return
        with open(file, "w") as F:
            F.write(content)
            PrintInColor.green(f"Example config file generated at {file}")
    else:
        PrintInColor.red(f"Directory {file_dir} does not exits")


def clear_history(_):
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
