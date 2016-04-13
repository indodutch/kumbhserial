# -*- coding: utf-8 -*-
"""
Created on Mon Apr 04 14:55:32 2016

@author: Zoli
"""

import serial
import time
import sys
try:
    import thread
except ImportError:
    import _thread as thread
import os
from .serial_tools import choose_serial_port, wait_for_user_quit


class KumbhMelaDumper(object):

    WAIT_FOR_DEVICE_TIMEOUT = 12

    def __init__(self, port, filename):
        try:
            self.comm = serial.Serial(port, 921600, timeout=1)
        except serial.SerialException as e:
            print(e)
            sys.exit()
        self.port = port
        self.run = True
        self.stopped = False
        self.file = open(filename, 'wb')
        self.recv_till = time.time()
        thread.start_new_thread(self.serial_recv_thread, ())
        thread.start_new_thread(self.heartbeat_thread, ())
            
    def serial_recv_thread(self):
        while self.run or time.time() < self.recv_till:
            line = self.comm.readline()
            self.file.write(line)
        print('read stopped')
        self.file.close()
        self.stopped = True

    def heartbeat_thread(self):
        while self.run:
            self.comm.write(b'@')
            time.sleep(1)
        print('heartbeat stopped')
            
    def stop(self):
        if self.run:
            self.recv_till = time.time() + self.WAIT_FOR_DEVICE_TIMEOUT
            self.run = False


def run_dumper(port):
    print('Reading ' + port + '. Type q or quit to quit.')
    port_id = port.split('/')[-1]
    if not os.path.exists('data/'):
        os.makedirs('data/')
    fname = 'data/dump' + port_id + time.strftime("%Y%m%d-%H%M%S") + '.txt'
    logger = KumbhMelaDumper(port, fname)
    try:
        wait_for_user_quit()
    except ValueError:
        print('Stopping ' + port)
        logger.stop()
        while not logger.stopped:
            time.sleep(1)
        print('Stopped.')

    return filename


def dumper_main():
    try:
        chosen_port = choose_serial_port()
        return run_dumper(chosen_port)
    except ValueError:
        print("Quit.")
    except KeyboardInterrupt:
        print("Force quit.")

if __name__ == "__main__":
    filename = dumper_main()
    if filename:
        print('serial data written into ' + filename)
