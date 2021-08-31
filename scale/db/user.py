import datetime

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model

import scale.db.udt as user_defined_types
from scale.common.variables import datacenter


__keyspace__ = "taas_user"
__dc_replication_map__ = {datacenter: 1}


class Plan(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "plan"

    user = columns.Text(
        primary_key=True,
        partition_key=True,
        index=True,
        required=True
    )
    name = columns.Text(
        primary_key=True,
        partition_key=True,
        required=True
    )
    target_platform = columns.Text(
        primary_key=True,
        partition_key=False,
        clustering_order="asc"
    )
    status = columns.Integer(default=1)
    runner_count = columns.List(columns.Integer, default=[1, 1])
    loop = columns.Boolean(default=True)
    wait_seconds_after_notify = columns.Integer(default=20)
    deployment_config = columns.Text()
    pods_adjust_momentum = columns.Integer(default=1)
    force_new_session = columns.Boolean(default=False)
    devices = columns.List(columns.Text(), default=[])
    description = columns.Text()
    created_at = columns.DateTime(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        default=datetime.datetime.utcnow
    )
    updated_at = columns.DateTime()
    duration = columns.Integer(default=24)


class Device(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "device"

    user = columns.Text(
        primary_key=True,
        partition_key=True,
        index=True,
        required=True
    )
    name = columns.Text(
        primary_key=True,
        partition_key=True,
        required=True
    )
    version = columns.Text()
    status = columns.Integer(default=1)
    protocol = columns.Text(default="ssh")
    type = columns.Text(
        primary_key=True,
        partition_key=False,
        clustering_order="asc",
        default="fgt"
    )
    credential = columns.Map(columns.Text, columns.Text)
    ip = columns.Text()
    logging = columns.List(
        columns.UserDefinedType(user_defined_types.Command)
    )
    created_at = columns.DateTime(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        default=datetime.datetime.utcnow
    )
    updated_at = columns.DateTime()


class Templates(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "templates"

    name = columns.Text(primary_key=True, partition_key=True, required=True)
    type = columns.Text(index=True)
    config_data = columns.Text()
    created_at = columns.DateTime(default=datetime.datetime.utcnow)
    updated_at = columns.DateTime(
        primary_key=True,
        partition_key=False,
        clustering_order="desc"
    )


class User(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "users"

    name = columns.Text(primary_key=True, partition_key=True, required=True)
    status = columns.Integer(default=1)
    email = columns.Text()
    access_level = columns.Integer(default=1)
    groups = columns.List(columns.UUID, default=[])
    created_at = columns.DateTime(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        default=datetime.datetime.utcnow
    )
    updated_at = columns.DateTime()


class Group(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "groups"

    name = columns.Text(primary_key=True)
    users = columns.List(columns.Text)
    access_level = columns.Integer(default=1)


class Session(Model):
    __keyspace__ = __keyspace__
    __table_name__ = "session"

    user = columns.Text(
        primary_key=True,
        partition_key=True,
        index=True
    )
    name = columns.Text(primary_key=True, partition_key=True)
    version = columns.Text()
    status = columns.Integer(default=1)
    target_platform = columns.Text()
    runner_count = columns.List(columns.Integer, default=[1, 1])
    loop = columns.Boolean(default=True)
    wait_seconds_after_notify = columns.Integer(default=20)
    deployment_config = columns.Text()
    pods_adjust_momentum = columns.Integer(default=1)
    force_new_session = columns.Boolean(default=False)
    command_log_targets = columns.List(
        columns.UserDefinedType(user_defined_types.Command)
    )
    test_cases = columns.List(columns.Text())
    dashboard_url = columns.Text()
    started_at = columns.DateTime(
        primary_key=True,
        partition_key=False,
        clustering_order="desc",
        default=datetime.datetime.utcnow
    )
    stopped_at = columns.DateTime()
