# pylint: disable=too-few-public-methods,too-many-arguments,unused-argument
import pymysql


class Database:
    """
    A base class for Database, can be used directly or derivatively
    """

    def __init__(self, db_ip, db_name, db_user, db_pw, db_port=3306):
        self.db_ip = db_ip
        self.db_name = db_name
        self.db_user = db_user
        self.db_pw = db_pw
        self.db_port = db_port
        self.conn = None

    def connect(self):
        self.conn = pymysql.connect(
            host=self.db_ip,
            port=int(self.db_port),
            database=self.db_name,
            user=self.db_user,
            password=self.db_pw,
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
        if self.conn:
            self.conn.close()

    def query_auto_connect(self, *args, **kwargs):
        try:
            self.connect()
            return self.query(*args, **kwargs)
        except Exception as e:
            ex = e
        finally:
            self.close()
        raise ex
