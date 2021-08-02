import datetime

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


__keyspace__ = "taas_user"
__replication_factor__ = 2


class Plan(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "plan"

    id = columns.UUID(primary_key=True, partition_key=True)
    user_id = columns.UUID(primary_key=True, partition_key=True, index=True)
    plan_name = columns.Text(required=True)
    target_platform = columns.Text(
        primary_key=True,
        partition_key=False,
        clustering_order="desc"
    )
    runner_count = columns.Integer(default=1)
    loop = columns.Boolean(default=True)
    wait_seconds_after_notify = columns.Integer(default=20)
    deployment_config = columns.Text()
    pods_adjust_momentum = columns.Integer(default=1)
    force_new_session = columns.Boolean(default=False)
    command_log_targets = columns.List(columns.UUID, default=[])
    created_at = columns.DateTime(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        default=datetime.datetime.utcnow()
    )
    updated_at = columns.DateTime()


class Commands(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "commands"

    id = columns.UUID(primary_key=True, partition_key=True)
    user_id = columns.UUID(primary_key=True, partition_key=True, index=True)
    name = columns.Text()
    protocol = columns.Text(default="ssh")
    type = columns.Text(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        default="fgt"
    )
    category = columns.Text()
    credential = columns.Map(columns.Text, columns.Text)
    commands = columns.List(columns.Text)
    created_at = columns.DateTime(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        default=datetime.datetime.utcnow()
    )
    updated_at = columns.DateTime()


class Templates(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "templates"

    id = columns.UUID(primary_key=True, partition_key=True)
    user_id = columns.UUID(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        index=True
    )
    name = columns.Text()
    template = columns.Text()
    created_at = columns.DateTime(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        default=datetime.datetime.utcnow()
    )
    updated_at = columns.DateTime()


class Users(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "users"

    id = columns.UUID(primary_key=True, partition_key=True)
    name = columns.Text()
    status = columns.Integer(default=1)
    email = columns.Text()
    created_at = columns.DateTime(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        default=datetime.datetime.utcnow()
    )


class Groups(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "groups"

    id = columns.UUID(primary_key=True)
    name = columns.Text()
    users = columns.List(columns.Text)


class Grants(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "grants"

    id = columns.UUID(primary_key=True)
    access_level = columns.Integer(default=1)
    grants = columns.Map(columns.UUID, columns.Integer)


class Runs(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "runs"

    id = columns.UUID(primary_key=True, partition_key=True)
    user = columns.Text(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        index=True
    )
    name = columns.Text()
    target_platform = columns.Text()
    runner_count = columns.Integer(default=1)
    loop = columns.Boolean(default=True)
    wait_seconds_after_notify = columns.Integer(default=20)
    deployment_config = columns.Text()
    pods_adjust_momentum = columns.Integer(default=1)
    force_new_session = columns.Boolean(default=False)
    command_log_targets = columns.Map(
        columns.Text, columns.List(columns.Text)
    )
    started_at = columns.DateTime(
        primary_key=True,
        partition_key=True,
        default=datetime.datetime.utcnow()
    )
    stopped_at = columns.DateTime()
