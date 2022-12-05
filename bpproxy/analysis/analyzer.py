# pylint: disable=invalid-sequence-index
import os
import re

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

from bpproxy.analysis.constants import ANALYZER_DEF
from utils.helper import dict_merge


def _is_section_title(section, line):
    # section = section.replace("(", "\\(").replace(")", "\\)")
    # section = section.replace("[", "\\[").replace("]", "\\]")
    return re.search(rf"\.\s({section})$", line)


def _parse_line(line):
    def check_append(value):
        try:
            ret.append(float(value))
        except ValueError:
            ret.append(value)

    curr = ""
    quote = False
    ret = []
    for c in line:
        if c in [","]:
            if not quote:
                check_append(curr)
                curr = ""
        elif c in ['"']:
            quote = not quote
        else:
            curr += c
    if curr:
        check_append(curr)
    return ret


class BpCsvData:
    def __init__(self, file_path, sections):
        self.file_path = file_path
        self.data = {}
        self._load_data(file_path, sections)

    def _load_data(self, file_path, sections):
        with open(file_path) as FILE:
            data = FILE.readlines()
        data.append("END OF FILE")
        section_list = list(sections.keys())
        tokenlized_row = [sec.split("/") for sec in section_list]
        tokenlized_head = list(list(zip(*tokenlized_row))[0])

        line_number = 0
        sec_idx = None
        token_list = []
        data_part = False
        data_csv = []
        columes = []
        processed = []
        while len(processed) < len(tokenlized_row) and line_number < len(data):
            line = data[line_number]
            if sec_idx is None:
                for idx, token in enumerate(tokenlized_head):
                    found = _is_section_title(token, line)
                    if found:
                        if idx not in processed:
                            token_list = tokenlized_row[idx][1:]
                            sec_idx = idx
                            break
            elif token_list:
                found = _is_section_title(token_list[0], line)
                if found:
                    token_list.pop(0)

            elif data_part:
                if "," in line:
                    data_csv.append(_parse_line(line.strip("\n")))
                else:
                    df = pd.DataFrame(data_csv, columns=columes)
                    self.data[sections[section_list[sec_idx]]] = df
                    data_csv = []
                    processed.append(sec_idx)
                    sec_idx = None
                    data_part = False
                    line_number = 0
            elif line.startswith("Timestamp") or line.startswith(
                    "time") or line.startswith("Measurement"):
                columes = line.strip("\n").split(",")
                data_part = True

            line_number += 1


class Analyzer(BpCsvData):
    def __init__(self, csv_path, category, custom_def=None):
        analyer_def = ANALYZER_DEF.copy()
        if custom_def:
            analyer_def = dict_merge(analyer_def, custom_def)
        self.defination = analyer_def.get(category)
        csv_sections = {}
        for k, v in self.defination.items():
            csv_sections[v.get("section")] = k
        super().__init__(csv_path, csv_sections)

        self.reference_ret = []

    def analyze(self):
        ref_def = self.defination.get("reference")
        if ref_def:
            func = getattr(self, ref_def.get("method"))
            ref_ret = func("reference")
            if ref_ret:
                self.reference_ret.append(ref_ret)
            else:
                raise ValueError(
                    f"Reference value not found, this maybe "
                    f"because running time is short"
                    f"{self.defination}"
                )
        data_def = self.defination.get("timeseries")
        if data_def:
            func = getattr(self, data_def.get("method"))
            return func("timeseries")
        raise ValueError("timeseries defination is required")

    def prepare_data(self, data_name):
        requirements = self.defination.get(data_name)
        data = self.data.get(data_name)
        if requirements:
            exp = requirements.get("except_range")
            if exp:
                data = pd.concat([
                    data[data["Timestamp"] < exp[0]],
                    data[data["Timestamp"] > exp[1]]
                ], ignore_index=True)
        return data

    def last_equal(self, data_name="timeseries"):
        requirements = self.defination.get(data_name)
        data: pd.DataFrame = self.prepare_data(data_name)
        columes = requirements.get("columns")
        threshold = requirements.get("threshold")
        threshold_value = threshold.get("value", 0)
        data["diff"] = (data[columes[1]] - data[columes[0]]).abs()
        ret = requirements.get("return", [])
        ds = data[data["diff"] > threshold_value]
        if len(ds) > 0:
            d = ds.iloc[0]
            return d[ret]

    def value_read_first_exist(self, data_name):
        requirements = self.defination.get(data_name)
        data: pd.DataFrame = self.prepare_data(data_name)
        if len(data) > 0:
            return data.iloc[0][requirements.get("return")]

    def value_read_ms_range(self, data_name):
        requirements = self.defination.get(data_name)
        threading_vale = requirements.get("thresholde_value", 100)
        data: pd.DataFrame = self.prepare_data(data_name)
        return_columns = requirements.get("return")
        if len(data) > 0:
            data["appAvgResponseTime"] = pd.to_numeric(
                data["appAvgResponseTime"])
            data = data.loc[
                data["appAvgResponseTime"] < threading_vale][return_columns]
            return data.iloc[-1]

    def value_read_without_reference(self, data_name):
        requirements = self.defination.get(data_name)
        ret_col = requirements.get("return")
        data: pd.DataFrame = self.prepare_data(data_name)
        column = requirements.get("column")
        if column:
            idx = data[column].idxmax()
            peak_timestamp = data.iloc[idx]
            return peak_timestamp[ret_col]
        raise ValueError("Column is required for max_from_begin method")

    @classmethod
    def max_from_begin(cls, data, timestamp, handler_param):
        column = handler_param.get("column")
        if column:
            idx = data[data["Timestamp"] <= timestamp][column].idxmax()
            return data.iloc[idx]
        raise ValueError("Column is required for max_from_begin method")

    @classmethod
    def last_record(cls, data, timestamp, handler_param):
        column = handler_param.get("column")
        if column:
            df = data[data["Timestamp"] <= timestamp]
            return df.iloc[-1]
        raise ValueError("Column is required for max_from_begin method")

    def smooth_data(self, data_name, data_colum):
        requirements = self.defination.get(data_name)
        window_length = requirements.get("window_length", 21)
        polyorder = requirements.get("polyorder", 3)
        ret = savgol_filter(data_colum, window_length, polyorder)
        return pd.DataFrame(ret)

    def gradient_to_zero(self, data_name):
        requirements = self.defination.get(data_name)
        ret_col = requirements.get("return")
        data: pd.DataFrame = self.prepare_data(data_name)
        gradient_column = requirements.get("columns")
        threas_hold = requirements.get("threshold", {})
        period = threas_hold.get("period", 10)
        thres_value = threas_hold.get("value", 0.01)
        smoothing_condition = requirements.get("smooth_data", False)
        if gradient_column and len(gradient_column) == 1:
            column = gradient_column[-1]
            if smoothing_condition:
                # was pct change method
                # data["pct_change"] = temp_smoothed_data.pct_change(
                #     periods=period).abs()
                temp_smoothed_data = self.smooth_data(data_name, data[column])
                temp_smoothed_data = temp_smoothed_data.to_numpy().reshape(-1)
                data["pct_change"] = pd.DataFrame(np.gradient(
                    temp_smoothed_data, period))
            else:
                tmp_column_data = data[column]
                tmp_column_data = tmp_column_data.to_numpy().reshape(-1)
                data["pct_change"] = pd.DataFrame(np.gradient(
                    tmp_column_data, period))
            df = data[data["pct_change"] <= thres_value].iloc[0]
            return df[ret_col]
        raise ValueError("Target gradient column is required and "
                         " only support one value")

    def gradient_to_explode(self, data_name):
        requirements = self.defination.get(data_name)
        ret_col = requirements.get("return")
        data: pd.DataFrame = self.prepare_data(data_name)
        gradient_column = requirements.get("columns")
        threas_hold = requirements.get("threshold", {})
        period = threas_hold.get("period", 10)
        thres_value = threas_hold.get("value", 0.6)
        smoothing_condition = requirements.get("smooth_data", False)
        if gradient_column and len(gradient_column) == 1:
            column = gradient_column[-1]
            if smoothing_condition:
                temp_smoothed_data = self.smooth_data(data_name, data[column])
                data["pct_change"] = temp_smoothed_data.pct_change(
                    periods=period).abs()
            else:
                data["pct_change"] = data[column].pct_change(
                    periods=period).abs()
            df = data[data["pct_change"] > thres_value].iloc[0]
            return df[ret_col]
        raise ValueError("Target gradient column is required and "
                         " only support one value")

    def value_read(self, data_name):
        if self.reference_ret:
            requirements = self.defination.get(data_name)
            ret_col = requirements.get("return")
            data: pd.DataFrame = self.prepare_data(data_name)
            handler = requirements.get("data_handler")
            if handler:
                method = handler.get("method")
                if method:
                    method = getattr(self, method)
                    ret = method(data, self.reference_ret.pop(), handler)
                    return ret[ret_col]
                raise ValueError("Method requried for data handler")
            raise ValueError("Data hander is required for value_read")
        raise AttributeError("reference is required for value_read method")

    def value_read_for_3peak(self, data_name):
        if self.reference_ret:
            requirements = self.defination.get(data_name)
            ret_col = requirements.get("return")
            data: pd.DataFrame = self.prepare_data(data_name)
            handler = requirements.get("data_handler")
            if handler:
                result_ret = pd.DataFrame()
                method = handler.get("method1")
                if method:
                    method = getattr(self, method)
                    ret = method(data, self.reference_ret.pop(), handler)
                    result_ret = pd.concat([result_ret, ret[ret_col]])
                method = handler.get("method2")
                if method:
                    method = getattr(self, method)
                    range_value_time = data.iloc[-1][ret_col[0]]
                    ret = method(data, range_value_time, handler)
                    ret = ret[ret_col]
                    result_ret = pd.concat([result_ret, ret])
                    method = handler.get("method3")
                    if method:
                        method = getattr(self, method)
                        peak_timestamp = ret[ret_col[0]]
                        ret = method(data, peak_timestamp, ret_col, handler)
                        result_ret = pd.concat([result_ret, ret])
                    for k, v in result_ret.items():
                        return v
                raise ValueError("Method requried for data handler")
            raise ValueError("Data hander is required for value_read")
        raise AttributeError("reference is required for value_read method")

    @classmethod
    def average_from_peak(cls, data, timestamp, ret_col, handler_param):
        data = data.loc[data["Timestamp"] < timestamp][ret_col]
        column = handler_param.get("column")
        if column:
            length_df = data.shape[0]
            if length_df >= 10:
                r_data = data.iloc[length_df - 19:length_df + 1][ret_col]
                average_value = r_data[column].mean()
                average_value = pd.DataFrame([average_value])
                average_value.index = ["Average MGB before peak"]
                return average_value
            raise ValueError(
                "Length of range(0, peak) dataframe is less than 10")
        raise ValueError("Column is required for max_from_begin method")

    def udt_reading_first_lower_value(self, data_name):
        requirements = self.defination.get(data_name)
        data: pd.DataFrame = self.prepare_data(data_name)
        columns = requirements["columns"]
        threshold_value = requirements["threshold_value"]
        threshold_value = int(threshold_value)
        if len(data) > 0:
            column_received = columns[-1]
            column_timestamp = columns[0]
            received_percent = data[column_received].str.split(expand=True)
            percent_list = received_percent[1].str.replace("%", "")
            percent_list = percent_list.astype(float)
            itemindex = np.where(percent_list < threshold_value)
            if len(itemindex[0]) > 1:
                itemindex = itemindex[0][0]
                return data[column_timestamp][itemindex]
            else:
                raise ValueError(
                    "Tune please, report did not receive threshold value!")

    def value_all_column(self, data_name):
        requirements = self.defination.get(data_name)
        data: pd.DataFrame = self.prepare_data(data_name)
        # columes = requirements.get("columns")
        ret = requirements.get("return", [])
        return data[ret]


if __name__ == "__main__":
    import yaml

    working_directory = os.getcwd()
    file_path = os.path.join(working_directory, "../report_def.yaml")
    with open(file_path) as F:
        custom_defs = yaml.safe_load(F)
    csv = Analyzer(
        r"/bp\benchmark_report\4737_mantis838968_QinQ_DI_321_YW2.csv",
        # r"C:\Users\zdouglas\Downloads\mantis838968_QinQ_DI_321_YW2_8.csv",
        "robot_test",
        custom_defs.get("report_def")).analyze()
    print(csv)
