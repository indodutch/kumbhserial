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
        try:
            while self.run or time.time() < self.recv_till:
                line = self.comm.readline()
                self.file.write(line)
            print('read stopped')
            self.file.close()
        finally:
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


def run_dumper(port, tmp_dir='data'):
    print('Reading ' + port + '. Type q or quit to quit.')
    port_id = port.split('/')[-1]
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    fname = os.path.join(tmp_dir, 'dump{0}{1}.txt'.format(
        port_id, time.strftime("%Y%m%d-%H%M%S")))
    logger = KumbhMelaDumper(port, fname)
    try:
        wait_for_user_quit()
    except ValueError:
        print('Stopping {0}...'.format(port))
        logger.stop()
        while not logger.stopped:
            time.sleep(1)
        print('Stopped.')
    finally:
        return fname


def dumper_main(chosen_port=None, tmp_dir='data'):
    try:
        if chosen_port is None:
            chosen_port = choose_serial_port()

        return run_dumper(chosen_port, tmp_dir=tmp_dir)
    except ValueError:
        print("Quit.")
    except KeyboardInterrupt:
        print("Force quit.")

if __name__ == "__main__":
    filename = dumper_main()
    if filename:
        print('serial data written into ' + filename)
