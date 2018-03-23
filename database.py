import mysql.connector


class Database():
    """Database to run query"""
    def __init__(self, arg):
        config = {
            'user': 'sherlock',
            'password': 'z00mrxr0cks!',
            'host': '69.164.196.100',
            'database': 'sherlock',
            'raise_on_warnings': True,
        }
        config.update(arg)
        self.connection = mysql.connector.connect(**config)
        self.cursor = self.connection.cursor()

    def execute(self, query):
        print query
        self.cursor.execute(query)
        if self.cursor.with_rows:
            return self.cursor.fetchall()
        return None

    def __del__(self):
        self.connection.commit()
        self.cursor.close()
        self.connection.close()
