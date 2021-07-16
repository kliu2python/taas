# pylint: disable=too-few-public-methods,too-many-arguments

from utils.db import Database


class Tables:
    TOKENS = 'tokens'
    USERS = 'users'
    ACCOUNTS = 'accounts'
    REALMS = 'realms'
    DEVICES = 'devices'
    CUSTOMERS = 'customers'
    CLUSTERS = 'clusters'


class FtcDatabase(Database):
    def query(self, table_name, key, value):
        cursor = self.conn.cursor()
        query = f'SELECT * FROM {table_name} WHERE {key}="{value}"'
        cursor.execute(query)
        all_items = cursor.fetchall()
        cursor.close()
        return all_items
