from datetime import datetime
import os
import config
import random
import time
import threading
import shutil
import sqlite3
from ACARSDecoderHandler import ACARSDecoderHandler
from ACARSServerHandler import ACARSServerHandler
import pprint

#For running shell commands
from subprocess import call

#For moving files
import shutil
pp = pprint.PrettyPrinter(indent=4)

debug = 1

def debug_print(input):
    if debug == 1:
        print("[DEBUG]: " + str(input))


#First check that our storage folder exists
if not os.access(config.db_storage_dir, os.R_OK or os.W_OK):
    try:
        os.mkdir(config.db_storage_dir)
    except OSError as err:
        print("Could not create the storage directory at " + config.db_storage_dir)
        print(err.strerror)
        exit()

#Check for the "old" data directory exists
if not os.access(config.old_storage_dir, os.R_OK or os.W_OK):
    try:
        os.mkdir(config.old_storage_dir)
    except OSError as err:
        print("Could not create the old storage directory at " + config.old_storage_dir)
        print(err.strerror)
        exit()

#Check for the logging directory exists
if not os.access(config.logging_dir, os.R_OK or os.W_OK):
    try:
        os.mkdir(config.logging_dir)
    except OSError as err:
        print("Could not create the logging directory at " + config.logging_dir)
        print(err.strerror)
        exit()

#Check for the master db directory exists
if not os.access(config.master_dir, os.R_OK or os.W_OK):
    try:
        os.mkdir(config.master_dir)
    except OSError as err:
        print("Could not create the logging directory at " + config.master_dir)
        print(err.strerror)
        exit()


#Then check if we have any 'leftover' databases around, and move them if so
storage_dir_contents = os.listdir(config.db_storage_dir)

for i in storage_dir_contents:
    if not os.path.isdir(config.db_storage_dir + "/" + i):
        try:
            shutil.move(config.db_storage_dir + "/" + i, config.old_storage_dir)
        except IOError as e:
            rand_add = str(randint(1,100))
            print( "Duplicate found, trying " + i + "/" + "-" + rand_add)
            shutil.move(config.db_storage_dir + "/" + i, config.old_storage_dir + "/"+ i + "/" + "-" + rand_add)

barrier = threading.Barrier(2)

# Get current date, generate name for it
current_filename_base = (datetime.now()).strftime("%Y%m%d-%H%M%S") + "-acars"
db_filename = config.db_storage_dir + "/" + current_filename_base + ".sqb"
srv_log = os.getcwd() + "/" + current_filename_base + "-srv.log"
dec_log = os.getcwd() + "/" + current_filename_base + "-dec.log"


debug_print("Server logging at " + srv_log)
debug_print("Decoder logging at " + dec_log)

#Init barrier to force bootup in the correct order (decoder then server)
acars_decoder = 0
acars_server = 0

#We don't want this to change between runs
current_filename_base = (datetime.now()).strftime("%Y%m%d-%H%M%S") + "-acars"
db_filename = config.db_storage_dir + "/" + current_filename_base + ".sqb"
master_db_filename = config.master_dir + "/" + config.master_db_name

#We do need to init the master DB if it isn't already
master_con = sqlite3.connect(master_db_filename)
master_cursor = master_con.cursor()

#Load the schema
schema_file = open(config.master_db_schema_path, "r")
schema = schema_file.read()
schema_file.close()

master_cursor.executescript(schema)
master_cursor.close()
master_con.close()

#We're also going to create the database to jam stuff into, so we can control its schema
temp_store_con = sqlite3.connect(db_filename)
temp_store_cursor = temp_store_con.cursor()

#Load the schema
schema_file = open(config.master_db_schema_path, "r")
schema = schema_file.read()
schema_file.close()

temp_store_cursor.executescript(schema)
temp_store_cursor.close()
temp_store_con.close()

try:
    while 1:
        logging_filename_base = (datetime.now()).strftime("%Y%m%d-%H%M%S") + "-acars"
        srv_log = config.logging_dir + "/" + logging_filename_base + "-srv.log"
        dec_log = config.logging_dir + "/" + logging_filename_base + "-dec.log"

        # Boot up the ACARS decoder
        acars_decoder = ACARSDecoderHandler("127.0.0.1:5555", "0", ["131.525", "131.725", "131.850"], dec_log, barrier)
        acars_decoder.start()

        # Boot up the ACARS server
        acars_server = ACARSServerHandler("*:5555", db_filename, srv_log, barrier)
        acars_server.start()

        #Now wait until our next backup
        time.sleep(config.backup_period)

        acars_server.stop()
        acars_decoder.stop()

        #Give the decoder etc chance to stop?
        time.sleep(2)

        #Take a copy of the database
        #This is mostly a 'just in case'
        copy_db_filename = config.db_storage_dir + "/" + logging_filename_base + "-backup.sqb"
        shutil.copyfile(db_filename, copy_db_filename)

        #Now we access the DB and empty the messages table
        con = sqlite3.connect(db_filename)
        cur = con.cursor()

        #First we attatch the master DB and copy the messages and new flights to it
        cur.execute("ATTACH DATABASE (?) AS (?)", (master_db_filename, "MASTER"))
        cur.execute("INSERT INTO MASTER.Messages SELECT * FROM main.Messages")
        #This only copies flights we haven't seen before
        cur.execute("INSERT INTO MASTER.Flights SELECT * FROM main.Flights WHERE NOT EXISTS(SELECT 1 FROM MASTER.Flights WHERE main.Flights.FlightID = MASTER.Flights.FlightID)")
        #Detach the master and delete the messages from the 'temporary' DB
        cur.execute("DETACH DATABASE 'MASTER'")
        cur.execute("DELETE FROM Messages")

        #Close and commit the changes
        cur.close()
        con.commit()
        con.close()
        # Add the DB name to the log
        f = open(config.logging_dir + "/" + "new_updates.log", "w")
        f.write(db_filename + "\n")
        f.close()


except KeyboardInterrupt:
    if isinstance(acars_decoder, ACARSDecoderHandler):
        acars_decoder.stop()
    if isinstance(acars_server, ACARSServerHandler):
        acars_server.stop()



# Wake up parent at midnight
#   Add the past days DB name to some log
#   Start the servers with the new log


## Might it be easier interface with the DB and just clear the entries?
