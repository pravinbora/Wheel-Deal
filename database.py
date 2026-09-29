import os
import sqlite3

from flask import current_app, g


class SQLiteCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, parameters=()):
        self._cursor.execute(query.replace('%s', '?'), parameters)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()


class SQLiteConnection:
    def __init__(self, connection):
        self._connection = connection

    def cursor(self):
        return SQLiteCursor(self._connection.cursor())

    def commit(self):
        self._connection.commit()


class SQLiteDatabase:
    def __init__(self, app):
        self.init_app(app)

    def init_app(self, app):
        app.teardown_appcontext(self.close)
        with app.app_context():
            self.initialize()

    @property
    def connection(self):
        if 'sqlite_connection' not in g:
            path = current_app.config['DATABASE_PATH']
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            connection = sqlite3.connect(path)
            connection.row_factory = self._dict_row
            g.sqlite_connection = SQLiteConnection(connection)
        return g.sqlite_connection

    @staticmethod
    def _dict_row(cursor, row):
        return {column[0]: row[index] for index, column in enumerate(cursor.description)}

    @staticmethod
    def close(_error=None):
        connection = g.pop('sqlite_connection', None)
        if connection is not None:
            connection._connection.close()

    def initialize(self):
        path = current_app.config['DATABASE_PATH']
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        connection = sqlite3.connect(path)
        try:
            schema_path = os.path.join(os.path.dirname(__file__), 'database.sql')
            with open(schema_path, encoding='utf-8') as schema_file:
                connection.executescript(schema_file.read())
        finally:
            connection.close()