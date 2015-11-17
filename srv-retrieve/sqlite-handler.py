import sqlite3
import os
import local_config

def _iterdump(connection, table_name):
    """
    Returns an iterator to dump a database table in SQL text format.
    """

    cu = connection.cursor()

    yield('BEGIN TRANSACTION;')

    # sqlite_master table contains the SQL CREATE statements for the database.
    q = """
       SELECT name, type, sql
        FROM sqlite_master
            WHERE sql NOT NULL AND
            type == 'table' AND
            name == :table_name
        """
    schema_res = cu.execute(q, {'table_name': table_name})
    for table_name, type, sql in schema_res.fetchall():
    #     if table_name == 'sqlite_sequence':
    #         yield('DELETE FROM sqlite_sequence;')
    #     elif table_name == 'sqlite_stat1':
    #         yield('ANALYZE sqlite_master;')
    #     elif table_name.startswith('sqlite_'):
    #         continue
    #     else:
    #         yield('%s;' % sql)

        # Build the insert statement for each row of the current table
        res = cu.execute("PRAGMA table_info('%s')" % table_name)
        column_names = [str(table_info[1]) for table_info in res.fetchall()]
        q = "SELECT 'INSERT INTO \"%(tbl_name)s\" VALUES("
        q += ",".join(["'||quote(" + col + ")||'" for col in column_names])
        q += ")' FROM '%(tbl_name)s'"
        query_res = cu.execute(q % {'tbl_name': table_name})
        for row in query_res:
            yield("%s;" % row[0])

db_list = ["20151115-050903-acars.sqb", "20151115-230910-acars.sqb", "20151116-050912-acars.sqb"]
table_list = ["Flights", "Messages", "Stations"]

#First check that our storage folder exists
if not os.access(local_config.master_db_dir, os.R_OK or os.W_OK):
    try:
        os.mkdir(local_config.master_db_dir)
    except OSError as err:
        print("Could not create the storage directory at " + local_config.master_db_dir)
        print(err.strerror)
        exit()

#Connect and define the cursor
master_con = sqlite3.connect(local_config.master_db_dir + "/" + local_config.master_db_name)
master_cursor = master_con.cursor()

#Load the schema
schema_file = open(local_config.master_db_schema_path, "r")
schema = schema_file.read()
schema_file.close()

#Run the schema - note that the schema should be written with IF NOT EXISTS
#There is no easy way to check if tables already exist in the DB
master_cursor.executescript(schema)

#Now we start to move data across
for db in db_list:
    print(local_config.db_storage_dir + "/" + db)
    sep_db_con = sqlite3.connect(local_config.db_storage_dir + "/" + db)

    for table in table_list:
        gen = _iterdump(sep_db_con, table)
        for command in gen:
            master_cursor.execute(command)
    # sep_db_cur = sep_db_con.cursor()
    # for table in table_list:
    #     sep_db_cur.execute("SELECT * FROM " + table)
    #     res = sep_db_cur.fetchall()
    #     print(res[1])

        #master_cursor.executemany("", sep_db_data[table])
