import sys

import psycopg2
from psycopg2.extensions import AsIs

class MyDataBase:
    def __init__(self, db="treschdeeplabcut", user="sam", password="postgres"):
        self.conn = psycopg2.connect(database=db, user=user, password=password)
        self.cur = self.conn.cursor()

    def query(self, query):
        self.cur.execute(query)
        print(self.cur.fetchall())
        
    def insertData(self, query, table_name):
        columns = query.keys()
        values = [query[column] for column in columns]

        insert_statement = 'INSERT INTO {} (%s) VALUES %s'.format(table_name)

        self.cur.execute(insert_statement, (AsIs(','.join(columns)), tuple(values)))
        self.conn.commit()
    
    
    def updateData(self, query, table_name):
        columns = query.keys()
        values = [query[column] for column in columns]

        update_statement = 'UPDATE {} SET (%s) = %s WHERE id = %s;'.format(table_name)

        self.cur.execute(update_statement, (AsIs(','.join(columns)), tuple(values), query['id']))
        self.conn.commit()

    def getData(self, table_name, column_name="*"):
        self.cur.execute("SELECT {} FROM {};".format(column_name, table_name))
        rows = self.cur.fetchall()

        return rows
    
    def getQueryData(self, query, table_name, column_name="*"):
        get_query_statement = "SELECT {} FROM {} WHERE subject_id = %s;".format(column_name, table_name)
        self.cur.execute(get_query_statement, (query['subject_id'],))

        rows = self.cur.fetchall()

        return rows


    def deleteData(self, query, table_name):
        delete_statement = 'DELETE FROM {} WHERE id = %s;'.format(table_name)

        self.cur.execute(delete_statement, (query['id'],))
        print(self.cur.mogrify(delete_statement, (query['id'],)))
        self.conn.commit()

    def countRow(self, table_name):
        self.cur.execute("SELECT * FROM {};".format(table_name))
        rows = self.cur.fetchall()

        i = 0
        for r in rows:
            i += 1
        return i

    def close(self):
        self.cur.close()
        self.conn.close()
