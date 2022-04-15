import re

from utils.logger import get_logger

LOGGER = get_logger("clear")
RE_CPU = re.compile(r"nice\s(.*?)%\sidle")
RE_MEM = re.compile(r"used\s\((.*?)%\)")
RE_BLADE_SLOTS_INFO = re.compile(r"Slot:\s(.*?)\s\s")
RE_DATA_PLAN_INFO = re.compile(r"states:\s(.*?)%(\r)?$")
CPU_IDX_MAPPING = {"-1": "dataplane", "-2": "MBD"}
CMD_PARSER_MAP = {
    "get system performance status": "parse_resouce_usage",
    "diagnose dpdk statistics show engine": "parse_dpdk_statics_drops_engine",
    "diagnose dpdk statistics show vnp": "parse_dpdk_statics_drops_vnp",
    "diagnose dpdk performance show": "parse_dpdk_perf_uage",
    "chassis_sync_status": "parse_chassis_sync_status"
}


class FortigateParser:
    @classmethod
    def split_cmdout(cls, cmd_out):
        """
        Split the command out put when we have multiple commands together
        """
        lines = cmd_out.split("\n")
        cmds = list(CMD_PARSER_MAP.keys())
        out = {}
        parsed = []
        curr = None

        for line in lines:
            line = line.rstrip("\r")
            for cmd in cmds:
                if re.search(rf"#(.*?){cmd}", line):
                    cmds.remove(cmd)
                    if curr:
                        out[CMD_PARSER_MAP[curr]] = parsed[1:]
                    parsed = []
                    curr = cmd
                    break
            if curr:
                parsed.append(line)

        if curr and parsed:
            out[CMD_PARSER_MAP[curr]] = parsed[1:]

        return out

    @classmethod
    def parse_chassis_sync_status(cls, synced):
        """
        This need parsed locally as the blade count is not fixed. only pass
        sync status here.
        """
        data = {
            "idx": "1",
            "counter": "chassie_sync",
            "value": synced[-1]
        }
        return [data]

    @classmethod
    def _parse_dpdk_statics_drops(cls, statics_type, cmd_out):
        data = []
        if cmd_out and isinstance(cmd_out, list):
            total = False
            for line in cmd_out:
                line = line.strip("\r")
                if line.startswith("----"):
                    continue
                if line:
                    if "Total" in line:
                        total = True
                        continue
                    if "drop" in line:
                        value_list = line.split(":")
                        value_list = list(filter(None, value_list))
                        value_type = value_list[0]
                        d = {
                            "idx": value_type,
                            "counter": f"dpdk-drop-{statics_type}",
                            "value": str(int(value_list[1]))
                        }
                        data.append(d)
                    if total and "Engine" in line:
                        break
        else:
            LOGGER.warning(
                "Can not parse dpdk cpu, due to no data or invalided data type"
                f"input type is {type(cmd_out)}"
            )
        return data

    @classmethod
    def parse_dpdk_statics_drops_engine(cls, cmd):
        return cls._parse_dpdk_statics_drops("engine", cmd)

    @classmethod
    def parse_dpdk_statics_drops_vnp(cls, cmd):
        return cls._parse_dpdk_statics_drops("vnp", cmd)

    @classmethod
    def parse_dpdk_perf_uage(cls, cmd_out):
        """
        parse output to get cpu usage for dkpk:
        FGT-PW-BMRK-X710 # diagnose dpdk performance show
        """
        data = []

        if cmd_out and isinstance(cmd_out, list):
            eng_list = []
            for line in cmd_out:
                line = line.strip("\r")
                if line.startswith("----"):
                    if eng_list:
                        eng_list = []
                    continue
                if line:
                    if not eng_list:
                        if "Average" in line:
                            eng_list.append("average")
                        elif "Engine" in line:
                            eng_list = list(
                                set(line.split(" ")) ^ {"Engine", ""}
                            )
                        continue

                    value_list = line.split(" ")[2:]
                    value_list = list(filter(None, value_list))
                    value_type = value_list.pop(0).strip(":")
                    for idx, v in zip(eng_list, value_list):
                        d = {
                            "idx": idx,
                            "counter": f"dpdk-cpu-{value_type}",
                            "value": v
                        }
                        data.append(d)
        else:
            LOGGER.warning(
                "Can not parse dpdk cpu, due to no data or invalided data type"
                f"input type is {type(cmd_out)}"
            )
        return data

    @classmethod
    def parse_resouce_usage(cls, cmd_out):
        data = []
        mbd_found = False
        module = "sys"
        idx = "-1"
        if cmd_out:
            for line_number, line in enumerate(cmd_out):
                v = None
                v_type = None
                d = None
                if "CPU " in line:
                    d = {}
                    v_type = "cpu"
                    v = str(100 - int(
                        RE_CPU.search(line).group(1)
                    ))
                    info_line = cmd_out[line_number - 1]
                    if info_line.startswith("Slot:"):
                        idx = (
                            RE_BLADE_SLOTS_INFO.search(info_line).group(1)
                        )
                        module = "blade"
                    elif info_line.startswith("MBD"):
                        idx = "-2"
                        mbd_found = True
                elif line.startswith("Memory:"):
                    d = {}
                    v_type = "memory"
                    v = RE_MEM.search(line).group(1)
                if mbd_found:
                    has_v = False
                    if line.startswith("Dataplane CPU"):
                        d = {}
                        v_type = "cpu"
                        idx = "-1"
                        has_v = True
                    elif line.startswith("Dataplane memory"):
                        d = {}
                        v_type = "memory"
                        has_v = True
                    if has_v:
                        v = str(
                            int(RE_DATA_PLAN_INFO.search(line).group(1))
                        )
                if d is not None:
                    d["idx"] = idx
                    d["counter"] = f"{module}-{v_type}"
                    d["value"] = v
                    data.append(d)
        return data

    @classmethod
    def parse(cls, cmd_out):
        outs = cls.split_cmdout(cmd_out)
        data = []

        for method, out in outs.items():
            try:
                d = getattr(cls, method)(out)
                if d:
                    data.extend(d)
            except Exception as e:
                LOGGER.exception(f"Error for parse data: {method}", exc_info=e)

        return data
