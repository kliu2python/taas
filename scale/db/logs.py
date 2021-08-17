import datetime
import uuid

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model

__keyspace__ = "taas_logs"
__replication_factor__ = 1


class Operation(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "operation"

    id = columns.UUID(
        primary_key=True, partition_key=True, default=uuid.uuid4()
    )
    datetime = columns.DateTime(
        primary_key=True, partition_key=True, default=datetime.datetime.utcnow()
    )
    user = columns.Text()
    source = columns.Text(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        index=True
    )
    log = columns.Text()


class Command(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "command"

    id = columns.UUID(
        partition_key=True, default=uuid.uuid4()
    )
    session_name = columns.Text(
        primary_key=True, partition_key=True, index=True
    )
    type = columns.Text(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
    )
    datetime = columns.DateTime(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        default=datetime.datetime.utcnow()
    )
    log = columns.Text()

    @classmethod
    def write(cls, session_name, log_type, log):
        cls.create(session_name=session_name, type=log_type, log=log)
