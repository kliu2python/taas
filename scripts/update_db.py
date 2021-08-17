import argparse

import utils.cassandra as db

args = None


def handle_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-u", "--user",
        dest="user",
        type=str,
        required=True,
        help="db user name"
    )
    parser.add_argument(
        "-p", "--password",
        dest="password",
        type=str,
        required=True,
        help="db password"
    )
    parser.add_argument(
        "-c", "--cluster-ip",
        dest="cluster_ips",
        nargs="+",
        required=True,
        help="cluster ips"
    )
    parser.add_argument(
        "-m", "--db-module",
        dest="db_module",
        type=str,
        required=True,
        help="schema defination module"
    )
    parser.add_argument(
        "--grant",
        dest="grant",
        action="store_true",
        required=False,
        default=False,
        help="specify if you want to add grants"
    )
    parser.add_argument(
        "--role",
        dest="role",
        type=str,
        required=False,
        default="taas",
        help="grant role name"
    )
    parser.add_argument(
        "--role-password",
        dest="role_password",
        type=str,
        required=False,
        default="taas",
        help="grant role password"
    )
    parser.add_argument(
        "--group",
        dest="group",
        type=str,
        required=False,
        default="taas_app",
        help="grant group name"
    )
    parser.add_argument(
        "--permission",
        dest="permission",
        nargs="+",
        required=False,
        default=["SELECT", "MODIFY"]
    )

    global args
    args = parser.parse_args()


def update_db():
    session = db.register_connection(args.cluster_ips, args.user, args.password)
    keyspaces = db.update_schema(args.db_module)
    if args.grant:
        db.grant_permissions(
            session,
            keyspaces,
            args.role,
            args.group,
            args.role_password,
            args.permission
        )


if __name__ == "__main__":
    handle_args()
    update_db()
