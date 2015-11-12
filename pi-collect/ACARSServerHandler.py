from threading import Thread
import config
import subprocess
import sys
import time

class ACARSServerHandler(Thread):
    def __init__(self, server_loc, db_path, logfile_path, barrier):
        Thread.__init__(self)
        self.server_location = server_loc
        self.db_path = db_path
        # self.base_station = base_station
        # self.store_duplicates = store_duplicates
        # self.store_ping_ack = store_ping_ack
        self.logfile_path = logfile_path
        self.stop_flag = False
        self.barrier = barrier


    def stop(self):
        self.stop_flag = True

    def run(self):
        self.barrier.wait()
        print("Starting ACARS server")
        with open(self.logfile_path, "w") as logfile:
            srv_proc = subprocess.Popen([config.acars_srv_dir + "/" + "./acarsserv", "-N", self.server_location, "-b", self.db_path, "-a", "-s", "-d"], stdout=logfile, stderr=logfile)
            while not self.stop_flag:
                time.sleep(1)
            srv_proc.terminate()
