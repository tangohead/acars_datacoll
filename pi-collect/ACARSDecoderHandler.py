from threading import Thread
import config
import subprocess
import time

class ACARSDecoderHandler(Thread):
    def __init__(self, server_loc, recv_num, freq_list, logfile_path, barrier):
        Thread.__init__(self)
        self.server_location = server_loc
        self.receiver_number = recv_num
        self.frequency_list = freq_list
        self.logfile_path = logfile_path
        self.stop_flag = False
        self.barrier = barrier

    def stop(self):
        self.stop_flag = True

    def run(self):
        print("Starting ACARS decoder")
        with open(self.logfile_path, "w") as logfile:

            dec_proc = subprocess.Popen([config.acars_dec_dir + "/" + "./acarsdec", "-N", self.server_location, "-r", self.receiver_number, self.frequency_list[0], self.frequency_list[1], self.frequency_list[2]], stdout=logfile, stderr=logfile)

        self.barrier.wait()
        while not self.stop_flag:
            time.sleep(1)
        dec_proc.terminate()
