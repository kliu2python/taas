import benchmark.db.logs as log_db
from utils.apibase import ApiBase


class ResultApi(ApiBase):
    __db_model__ = log_db.Result


class CounterApi(ApiBase):
    __db_model__ = log_db.Counter


class CrashLogApi(ApiBase):
    __db_model__ = log_db.CrashLog


class ConsoleLogApi(ApiBase):
    __db_model__ = log_db.ConsoleLog


class CommandLogApi(ApiBase):
    __db_model__ = log_db.CommandLog
