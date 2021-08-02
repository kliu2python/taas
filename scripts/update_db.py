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

    global args
    args = parser.parse_args()


def update_db():
    db.register_connection(args.cluster_ips, args.user, args.password)
    db.update_schema(args.db_module)


if __name__ == "__main__":
    handle_args()
    update_db()
