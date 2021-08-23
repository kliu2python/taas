import pandas as pd

import scale.db.logs as user_logs
from scale.services.base import ApiBase


class CommandLog(ApiBase):
    __db_model__ = user_logs.Command

    @classmethod
    def get_logs(
            cls, session_name, log_type, sort=True, to_list=False, **filters,
    ):
        logs = cls.read_all(
            session_name=session_name,
            type=log_type,
            **filters
        )
        if sort and logs:
            df = pd.DataFrame(logs)
            df["datetime"] = pd.to_datetime(df["datetime"])
            df.sort_values(by=["datetime"], inplace=True, ascending=False)
            if to_list:
                logs = df.to_dict("records")
            else:
                logs = df
        return logs
