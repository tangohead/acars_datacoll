from datetime import datetime
import os
import config
import random
import time
import threading
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

try:
    while 1:
        current_filename_base = (datetime.now()).strftime("%Y%m%d-%H%M%S") + "-acars"
        db_filename = config.db_storage_dir + "/" + current_filename_base + ".sqb"
        srv_log = config.logging_dir + "/" + current_filename_base + "-srv.log"
        dec_log = config.logging_dir + "/" + current_filename_base + "-dec.log"

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

        # Add the DB name to the log
        f = open(config.logging_dir + "/" + "new_updates.log", "w")
        f.write(db_filename)
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