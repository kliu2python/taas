import datetime
import random

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model

__keyspace__ = "taas_logs"
__replication_factor__ = 1


def _random_log_index():
    return random.randrange(1, 100)


class Operation(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "operation"

    user = columns.Text()
    source = columns.Text(
        primary_key=True,
        partition_key=True
    )
    datetime = columns.DateTime(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        default=datetime.datetime.utcnow
    )
    log = columns.Text()


class Command(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "command"

    session_name = columns.Text(
        primary_key=True, partition_key=True
    )
    type = columns.Text(primary_key=True, partition_key=True)
    datetime = columns.DateTime(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        default=datetime.datetime.utcnow
    )
    log_index = columns.Integer(
        primary_key=True,
        partition_key=True,
        default=_random_log_index
    )
    log = columns.Text()


class CaseHistory(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "casehistory"

    session_name = columns.Text(
        primary_key=True, partition_key=True, index=True
    )
    runner_name = columns.Text(primary_key=True, partition_key=True)
    case_name = columns.Text()
    datetime = columns.DateTime(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        default=datetime.datetime.utcnow
    )
    log_index = columns.Integer(
        primary_key=True,
        partition_key=True,
        default=_random_log_index
    )
    result = columns.Text()
    log = columns.Text()
    failure_id = columns.UUID()


class FailureLog(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "failurelog"

    id = columns.UUID(
        primary_key=True, partition_key=True
    )
    datetime = columns.DateTime(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        default=datetime.datetime.utcnow
    )
    log = columns.List(columns.Text)
