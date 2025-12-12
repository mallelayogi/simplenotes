import mysql.connector.pooling
from flask import current_app, g
# This global variable will hold the connection pool
db_pool = None
def get_db_pool():
    """
    Returns the application-wide database connection pool.
    Initializes it if it doesn't exist.
    """
    global db_pool
    if db_pool is None:
        db_config = {
            "database": "Ramu$snm_db",
            "user": "Ramu",
            "password": "Ramu@123",
            "host": "Ramu.mysql.pythonanywhere-services.com",
            # Add other necessary configurations like port
        }
        # Create the connection pool
        db_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="mysql_connection_pool",
            pool_size=5, # Define the pool size
            **db_config
        )
    return db_pool

def get_db_connection():
    """
    Retrieves a connection from the pool and stores it in the application context 'g'.
    """
    if 'db_conn' not in g:
        g.db_conn = get_db_pool().get_connection()
    return g.db_conn

def close_db_connection(e=None):
    """
    Closes the connection when the request ends and returns it to the pool.
    """
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()