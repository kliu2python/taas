import datetime
import uuid

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from scale.common.variables import datacenter

__keyspace__ = "taas_logs"
__dc_replication_map__ = {datacenter: 1}


class Operation(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "operation"

    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    source = columns.Text()
    user = columns.Text()
    datetime = columns.DateTime(
        primary_key=True,
        clustering_order="desc",
        default=datetime.datetime.utcnow
    )
    log = columns.Text()


class Command(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "command"

    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    session_name = columns.Text(index=True)
    type = columns.Text()
    datetime = columns.DateTime(
        primary_key=True,
        clustering_order="desc",
        default=datetime.datetime.utcnow
    )
    log = columns.Text()


class CaseHistory(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "casehistory"

    id = columns.UUID(partition_key=True, default=uuid.uuid4)
    session_name = columns.Text(index=True)
    runner_name = columns.Text()
    case_name = columns.Text()
    datetime = columns.DateTime(
        primary_key=True,
        clustering_order="desc",
        default=datetime.datetime.utcnow
    )
    result = columns.Text()
    log = columns.Text()
    failure_id = columns.UUID()


class FailureLog(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "failurelog"

    id = columns.UUID(primary_key=True)
    session_name = columns.Text(index=True)
    datetime = columns.DateTime(
        primary_key=True,
        clustering_order="desc",
        default=datetime.datetime.utcnow
    )
    log = columns.List(columns.Text)


class Pictures(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "pictures"

    id = columns.UUID(primary_key=True)
    session_name = columns.Text(index=True)
    uploader_name = columns.Text()
    session_numbers = columns.Integer(
        primary_key=True,
        clustering_order="desc"
    )
    iteration = columns.Integer(default=0)
    category = columns.Text()
    imgb64 = columns.Text()
