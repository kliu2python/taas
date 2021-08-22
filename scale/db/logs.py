import datetime
import uuid

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model

__keyspace__ = "taas_logs"
__replication_factor__ = 1


class Operation(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "operation"

    source = columns.Text(
        primary_key=True,
        partition_key=True
    )
    id = columns.UUID(partition_key=True, default=uuid.uuid4)
    user = columns.Text()
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
    id = columns.UUID(partition_key=True, default=uuid.uuid4)
    type = columns.Text()
    datetime = columns.DateTime(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        default=datetime.datetime.utcnow
    )
    log = columns.Text()


class CaseHistory(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "casehistory"

    session_name = columns.Text(
        primary_key=True, partition_key=True, index=True
    )
    id = columns.UUID(partition_key=True, default=uuid.uuid4)
    runner_name = columns.Text()
    case_name = columns.Text()
    datetime = columns.DateTime(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        default=datetime.datetime.utcnow
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
