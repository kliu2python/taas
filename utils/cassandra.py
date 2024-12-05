import os
import importlib
import inspect

from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.cqlengine import connection
from cassandra.cqlengine.models import Model
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.management import (
    create_keyspace_network_topology,
    create_keyspace_simple
)
from cassandra.policies import ConstantReconnectionPolicy

from utils.logger import get_logger

logger = get_logger()
os.environ["CQLENG_ALLOW_SCHEMA_MANAGEMENT"] = "true"


def register_connection(
        cluster_ips, username, password, name="default", default=True
):
    auth = PlainTextAuthProvider(username=username, password=password)
    if isinstance(cluster_ips, str):
        cluster_ips = [cluster_ips]
    print(f"IP of cluster is {cluster_ips}, and auth is {username}/{password}")
    cluster = Cluster(
        cluster_ips,
        auth_provider=auth,
        reconnection_policy=ConstantReconnectionPolicy(delay=1)
    )
    session = cluster.connect()
    connection.register_connection(
        name,
        session=session,
        default=default
    )
    return session


def update_schema(schema_module):
    root_path = os.path.dirname(os.path.dirname(__file__))
    module_list = schema_module.split(".")
    module_path = os.path.join(root_path, *module_list)
    db_files = os.listdir(module_path)
    updated_keyspaces = []

    for file in db_files:
        if not file.startswith("_") and file.endswith(".py"):
            file = file.rstrip(".py")
            module = importlib.import_module(f"{schema_module}.{file}")
            dc_rep_map = getattr(module, "__dc_replication_map__", None)
            rep_factor = getattr(module, "__replication_factor__", None)
            if hasattr(module, "__keyspace__"):
                keyspace = module.__keyspace__
                updated_keyspaces.append(keyspace)
                if dc_rep_map:
                    create_keyspace_network_topology(
                        keyspace,
                        dc_rep_map
                    )
                elif rep_factor is not None:
                    if rep_factor > 0:
                        create_keyspace_simple(
                            keyspace,
                            rep_factor
                        )
                    else:
                        raise ValueError(
                            "replication_factor should greater than 0"
                        )
                else:
                    logger.error("No replication type specified "
                                 "or file has no __keyspace__ defined")
                    continue

                for class_name in dir(module):
                    if (
                            not class_name.startswith("_")
                            and class_name not in ["Model"]
                    ):
                        obj = getattr(module, class_name)
                        if inspect.isclass(obj) and issubclass(obj, Model):
                            logger.info(f"Updating {obj.__name__}")
                            sync_table(obj)

    return updated_keyspaces


def grant_permissions(
        session,
        keyspaces,
        role,
        group,
        password,
        permissions=None
):
    logger.info("Grant User permissions")
    if permissions is None:
        permissions = ["SELECT", "MODIFY"]
    commands = [
        f"CREATE ROLE {group}",
        f"CREATE ROLE {role} with LOGIN = true and PASSWORD = '{password}'",
        f"GRANT {group} to {role}"
    ]

    for keyspace in keyspaces:
        for permission in permissions:
            commands.append(
                f"GRANT {permission} on KEYSPACE {keyspace} to {group}"
            )

    for cmd in commands:
        try:
            session.execute(cmd)
        except Exception as e:
            logger.warning(e)

    res = session.execute(f"LIST ALL PERMISSIONS of {group}")
    return res
