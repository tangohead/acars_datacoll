import paramiko
from paramiko import SSHClient
from paramiko import SSHException

from scp import SCPClient

#for file ops
import os

import local_config
import remote_config

import sqlite3
#First check that our storage folder exists
if not os.access(local_config.db_storage_dir, os.R_OK or os.W_OK):
    try:
        os.mkdir(local_config.db_storage_dir)
    except OSError as err:
        print("Could not create the storage directory at " + config.db_storage_dir)
        print(err.strerror)
        exit()

ssh = SSHClient()
ssh.load_system_host_keys()
ssh.load_host_keys(local_config.local_host_keys_path)

#Not recommended, but needed as for some reason it wouldn't recognise abe
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('abe.cs.ox.ac.uk', port=2150, username="pi", key_filename=local_config.pi_collect_key_path)
except SSHException as e:
    print(e)

#Grab the log containing the new filenames
#with SCPClient
scp = SCPClient(ssh.get_transport())

scp.get(remote_config.logging_dir + "/" + "new_updates.log")

#Copy database over into storage directory
f = open("new_updates.log", 'r')
retrieved_db_paths = []
for line in f:
    retrieved_db = line[:-1]
    scp.get(retrieved_db, local_config.db_storage_dir)
    retrieved_db_paths.append(local_config.db_storage_dir + "/" + line.split("/")[-1])


ssh.exec_command("cat '' > " + remote_config.logging_dir + "/" + "new_updates.log")

print(retrieved_db)

#Merge new DBs with master? Keep originals
