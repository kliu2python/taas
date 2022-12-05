import re


IN_SYNC_RE = re.compile(r"in_sync=(.*?)$")
ANALYZER_DEF = {
    "udp_throughput": {
        "timeseries": {
            "section": "Aggregate Stats/Detail/Ethernet Data Rates",
            "method": "last_equal",
            "columns": ["Transmit rate", "Receive rate"],
            "threshold": {
                "value": 0,
                "period": 10
            },
            "except_range": [0, 20],
            "unit": "Mbps",
            "return": ["Timestamp", "Receive rate"]
        }
    },
    "tcp_cc": {
        "timeseries": {
            "section": "Test Results for Aggregated Session Sender/"
                       "Detail/TCP Concurrent Connections",
            "method": "gradient_to_zero",
            "except_range": [0, 20],
            "columns": ["Server"],
            "threshold": {
                "value": 0.1,
                "period": 10
            },
            "return": ["Timestamp", "Server"]
        }
    },
    "tcp_cps": {
        "reference": {
            "section": "Test Results for Aggregated Application Simulator/"
                       "Detail/TCP Concurrent Connections",
            "method": "gradient_to_explode",
            "columns": ["Server"],
            "except_range": [0, 20],
            "threshold": {
                "value": 0.5,
                "period": 10
            },
            "return": "Timestamp"
        },
        "timeseries": {
            "section": "Test Results for Aggregated Application Simulator/"
                       "Detail/TCP Connection Rate",
            "method": "value_read",
            "data_handler": {
                "method": "last_record",
                "column": "Server establish rate"
            },
            "except_range": [0, 20],
            "return": ["Timestamp", "Server establish rate"]
        }
    },
    "http_cps": {
        "reference": {
            "section": "Test Results for Aggregated Client Simulation/"
                       "Detail/TCP Concurrent Connections",
            "method": "gradient_to_explode",
            "columns": ["Server"],
            "except_range": [0, 20],
            "threshold": {
                "value": 0.5,
                "period": 10
            },
            "return": "Timestamp"
        },
        "timeseries": {
            "section": "Test Results for Aggregated Client Simulation/"
                       "Detail/TCP Connection Rate",
            "method": "value_read",
            "data_handler": {
                "method": "last_record",
                "column": "Server establish rate"
            },
            "except_range": [0, 20],
            "return": ["Timestamp", "Server establish rate"]
        }
    },
    "tcp_throughput": {
        "reference": {
            "section": "Test Results for Aggregated Application Simulator"
                       "/Detail/Flow Exceptions \\(All\\)",
            "method": "value_read_first_exist",
            "except_range": [0, 20],
            "return": "Timestamp"
        },
        "timeseries": {
            "section": "Aggregate Stats/Detail/Ethernet Data Rates",
            "method": "value_read",
            "data_handler": {
                "method": "max_from_begin",
                "column": "Receive rate"
            },

            "unit": "Mbps",
            "return": ["Timestamp", "Receive rate"]
        }
    }
}
