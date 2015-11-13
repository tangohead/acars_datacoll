import paramiko
from paramiko import SSHClient
from paramiko import SSHException
from paramiko import AutoAddPolicy
from scp import SCPClient
import local_config

ssh = SSHClient()
ssh.load_system_host_keys()
ssh.load_host_keys(local_config.local_host_keys_path)

#Not recommended, but needed as for some reason it wouldn't recognise abe
ssh.set_missing_host_key_policy(AutoAddPolicy)
try:
    ssh.connect('abe.cs.ox.ac.uk', port=2150, username="pi", key_filename=local_config.pi_collect_key_path)
except SSHException as e:
    print(e)
print(ssh.exec_command('ls'))

#Grab the log containing the new filenames
#with SCPClient

#Check that the directory to store in exists

#Copy database over into storage directory

#Merge new DBs with master? Keep originals
