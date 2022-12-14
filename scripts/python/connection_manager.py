import psycopg2
import pandas as pd


class Manager():
    """
    a python class used to manage connection with posgres server 
    and the execution of sql queries
    """
    def __init__(self):
        pass
        
    def connect_to_server(self,
                        host:str = "localhost", 
                        port:int=5432, 
                        user:str = "warehouse", 
                        password:str="warehouse", 
                        dbName:str="warehouse"):
        """
        A function that allows you to connect to postgreSQL database
        Args:
            host: ip address or domain
            user: the user of the server
            password: the password to server
            dbName: the name of the server

        Returns:
            connection: connection object
            cursor: cursor object

        """
        try:
            conn = psycopg2.connect(
                                host=host,
                                port=port,
                                database=dbName,
                                user=user,
                                password=password)
            cur = conn.cursor()
            print(f"successfully connected; cursor: {cur}")
            return conn, cur
        except Exception as e:
            print(f"Error: {e}")


    def close_connection(self, connection, cursor):
        """
        closes connection with database.

        Args: 
            connection: mysql connection object
            cursor: cursor object

        Returns: None.
        """
        connection.commit()
        cursor.close()
        print("connection closed and transaction committed")


    def execute_query(self, cursor, file_sql) -> None:
        """
        A function to execute sql queries
        
        Args:
            cursor: cursor object
            file_sql: the location of the sql query file
            dbName: the name of the database

        Returns: None
        """
        sqlFile = file_sql
        fd = open(sqlFile, 'r')
        readsqlFile = fd.read()
        fd.close()
        sqlQueries = readsqlFile.split(';')
        for query in sqlQueries:
            try:
                cursor.execute(query)
                # try:
                #     rows = cursor.fetchall()    # get all selected rows, as Barmar mentioned
                #     for r in rows:
                #         print(r)
                # except Exception as e:
                #     print(f"Inner error: {e}")
                print("successfully executed")
            except Exception as e:
                print('command skipped: ', query)
                print(e)


    def fetch_data(self, conn, table = "warehouse", columns=None, limit=1000000):
        """
        Args:
            cur: cursor to communicate with database.
            limit: the number of rows to return
        Returns:
            result: iteratable object that holds all values of a query
        """
        cols = "*"
        if (columns is not None):
            cols = columns

        query = f""" select {cols} from {table} limit {limit}"""

        try:
            results = pd.read_sql_query(query, conn)
            return results
        except Exception as e:
            print(f"error: {e}")


    def close_connection(self, connection, cursor):
        """
        closes connection with database.

        Args: 
            connection: mysql connection object
            cursor: cursor object

        Returns: None.
        """
        print("connection closed and transaction committed")


    def create_table(self, cursor, file_sql, dbName: str) -> None:
        """
        A function to create SQL table
        
        Args:
            cursor: cursor object
            file_sql: the location of the sql table creation query file
            dbName: the name of the database

        Returns: None
        """
        sqlFile = file_sql
        fd = open(sqlFile, 'r')
        readsqlFile = fd.read()
        fd.close()
        sqlCommands = readsqlFile.split(';')
        for command in sqlCommands:
            try:
                result = cursor.execute(command)
                print(f"table created successfully")
            except Exception as e:
                print('command skipped: ', command)
                print(e)


    def insert_into_table(self, cursor, connection, dbName: str, df: pd.DataFrame, table_name: str) -> None:
        """
        A function to insert values in SQL table
        Args:
            cursor: cursor object
            connection: mysql connection object
            dbName: database name
            df: dataframe that holds the data
            table_name: the name of the table to store the data in
        
        Returns: None.
        """
        for _, row in df.iterrows():
            sqlQuery = f"""INSERT INTO {table_name} 
            (track_id, types, traveled_d, avg_speed, trajectory)
                  VALUES(%s, %s, %s, %s, %s);"""

            data = (row[0], row[1], row[2], row[3], (row[4]))
            try:
                cursor.execute(sqlQuery, data)
                connection.commit()
            except Exception as e:
                connection.rollback()
                print(e)
        print('Data inserted successfully')

if __name__=="__main__":
    pass
