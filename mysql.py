""" Handles basic SQL database connection/execution """

import pymysql
import config
from env import CONSTANTS

class Database:
    """ Database class to handle SQL connection/execution """

    def execute(self, statement):
        """ Run a pre-formed database query """
        self.cursor.execute(statement)
        return self.cursor.fetchall()

    def commit(self):
        """ Commit changes made in previous queries """
        self.database.commit()

    def __init__(self):
        """ Create a connection to the SQL instance """
        self.database = pymysql.connect(
            "localhost",
            CONSTANTS['sql_user'],
            config.MYSQL['pass'],
            CONSTANTS['sql_database'],
            cursorclass=pymysql.cursors.DictCursor
        )

        self.cursor = self.database.cursor()

    def disconnect(self):
        """ Cleanly close database connection """
        self.database.close()
