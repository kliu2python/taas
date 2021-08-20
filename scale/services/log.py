import scale.db.logs as user_logs
from scale.services.base import ApiBase


class CommandLog(ApiBase):
    __db_model__ = user_logs.Command

    @classmethod
    def get_logs(cls, session_name, log_type, limit=0):
        logs = cls.read(
            "log",
            limit=limit,
            order_by=["datetime"],
            session_name=session_name,
            type=log_type
        )
        return logs.get("log")
