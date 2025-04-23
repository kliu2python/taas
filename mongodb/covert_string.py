# at top of your module
import json
from datetime import datetime
from dateutil.parser import isoparse   # pip install python-dateutil


def _parse_date_filters(obj):
    """
    Recursively convert any { '$gte': '2025-04-20T00:00:00', ... }
    into { '$gte': datetime(...), ... }
    """
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            # for comparison operators with ISO‑string values
            if k in ("$gte", "$lte", "$gt", "$lt") and isinstance(v, str):
                try:
                    new[k] = isoparse(v)
                except ValueError:
                    new[k] = v
            else:
                new[k] = _parse_date_filters(v)
        return new

    elif isinstance(obj, list):
        return [_parse_date_filters(i) for i in obj]

    else:
        return obj
