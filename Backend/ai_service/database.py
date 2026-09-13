import mysql.connector


def get_database_connection():

    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="mysql",
        database="talentiq_db"
    )

    return connection