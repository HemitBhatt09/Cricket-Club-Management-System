# db.py

import mysql.connector

def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Hemit@2006",
        database="dbms_ccms"
    )
    return connection   