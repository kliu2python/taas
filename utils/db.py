# pylint: disable=too-few-public-methods,too-many-arguments,unused-argument
import pymysql


class Database:
    """
    A base class for Database, can be used directly or derivatively
    """

    def __init__(self, db_ip, db_name, db_user, db_pw, db_port=3306):
        self.conn = pymysql.connect(
            host=db_ip,
            port=int(db_port),
            database=db_name,
            user=db_user,
            password=db_pw,
            cursorclass=pymysql.cursors.DictCursor
        )
        self.conn.autocommit(True)

    def query(self, *args, **kwargs):
        cursor = self.conn.cursor()
        cursor.execute(kwargs.get("query"))
        all_items = cursor.fetchall()
        cursor.close()
        return all_items

    def close(self):
        self.conn.close()
