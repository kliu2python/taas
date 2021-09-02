import datetime

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from benchmark.common.variables import datacenter

__keyspace__ = "benchmark"
__dc_replication_map__ = {datacenter: 1}


class Result(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "results"
    __unique_values__ = False

    job_name = columns.Text(primary_key=True, partition_key=True)
    build_id = columns.Text(primary_key=True, partition_key=True)
    test = columns.Text()
    platform = columns.Text()
    version = columns.Text()
    user = columns.Text(index=True)
    settings = columns.Text()
    start_time = columns.DateTime()
    end_time = columns.DateTime()
    result = columns.Text()


class CaseInfo(Model):
    __keyspace__ = __keyspace__
    __table_name = "caselog"
    __unique_values__ = False

    job_name = columns.Text(primary_key=True, partition_key=True)
    build_id = columns.Text(primary_key=True, partition_key=True)
    case_name = columns.Text()
    start_time = columns.DateTime(
        primary_key=True,
        clustering_order="desc",
        default=datetime.datetime.now
    )
    end_time = columns.DateTime()


class Counter(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "counters"
    __unique_values__ = False

    job_name = columns.Text(primary_key=True, partition_key=True)
    build_id = columns.Text(primary_key=True, partition_key=True)
    case_name = columns.Text()
    counter = columns.Text()
    idx = columns.Text()
    datetime = columns.Integer(
        primary_key=True,
        clustering_order="desc"
    )
    value = columns.Text()


class CrashLog(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "crashlogs"
    __unique_values__ = False

    job_name = columns.Text(primary_key=True, partition_key=True)
    build_id = columns.Text(primary_key=True, partition_key=True)
    datetime = columns.DateTime(
        primary_key=True,
        partition_key=True,
        default=datetime.datetime.now
    )
    platform = columns.Text()
    version = columns.Text()
    test = columns.Text(required=False)
    log = columns.Text()


class CommandLog(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "commandlogs"
    __unique_values__ = False

    job_name = columns.Text(primary_key=True, partition_key=True)
    build_id = columns.Text(primary_key=True, partition_key=True)
    datetime = columns.DateTime(
        primary_key=True,
        partition_key=True,
        default=datetime.datetime.now
    )
    command = columns.List(columns.Text)
    log = columns.Text()
