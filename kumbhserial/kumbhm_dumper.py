# -*- coding: utf-8 -*-
"""
Created on Mon Apr 04 14:55:32 2016

@author: Zoli
"""

import serial
import time
import sys
import threading
import os
from .serial_tools import choose_serial_port, text_in
from .heartbeat import Heartbeat


class KumbhMelaReader(threading.Thread):

    WAIT_FOR_DEVICE_TIMEOUT = 12

    def __init__(self, port, appender):
        super(KumbhMelaReader, self).__init__()
        self.comm = serial.Serial(port, 921600, timeout=1)
        self.port = port
        self.is_done = False
        self.appender = appender
        self.recv_till = time.time()
        self.heartbeat = Heartbeat(self.comm)
        self.exception = None

    def start(self):
        super(KumbhMelaReader, self).start()
        self.heartbeat.start()

    def run(self):
        print('started logger')
        try:
            while not self.is_done or time.time() < self.recv_till:
                line = self.comm.readline()
                self.appender.append_line(line)
            print('read stopped')
        except Exception as ex:
            self.exception = ex
            print('read or write failed, press ENTER to quit.')

    def join(self, timeout=None):
        try:
            super(KumbhMelaReader, self).join(timeout=timeout)
        finally:
            self.appender.done()

    def done(self):
        if not self.is_done:
            self.is_done = False
            self.recv_till = (time.time() +
                              KumbhMelaReader.WAIT_FOR_DEVICE_TIMEOUT)
            self.heartbeat.done()



class Heartbeat(threading.Thread):
    def __init__(self, comm, sleep=1):
        super(Heartbeat, self).__init__()
        self.comm = comm
        self.sleep = sleep
        self.is_done = False

    def run(self):
        print('Heartbeat started')
        try:
            while not self.is_done:
                self.comm.write(b'@')
                time.sleep(1)
        except:
            print('Sending heartbeat failed')
            raise

        print('Heartbeat finished')

    def done(self):
        self.is_done = True


class Dumper(object):
    def __init__(self, path):
        self.file = open(path, 'wb')

    def append_line(self, data):
        self.file.write(data)

    def done(self):
        self.file.close()


def create_dumper_file(port, tmp_dir='data'):
    port_id = port.split('/')[-1]
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    return os.path.join(tmp_dir, 'dump-{0}{1}.txt'.format(
        port_id, time.strftime("%Y%m%d-%H%M%S")))


def wait_on_reader(reader):
    try:
        while reader.exception is None:
            text_in() # waiting for user input
        if reader.exception:
            print('Failed to communicate: {0}'.format(reader.exception))
    except ValueError:
        print('Stopping {0}...'.format(reader.port))
    finally:
        reader.done()
        reader.join(KumbhMelaReader.WAIT_FOR_DEVICE_TIMEOUT + 1)
        print('Stopped {0}.'.format(reader.port))


def run_reader(port, appender):
    print('Reading ' + port + '. Type q or quit to quit.')
    reader = KumbhMelaReader(port, appender)
    print('Starting {0}...'.format(port))
    reader.start()
    wait_on_reader(reader)

def dumper_main(chosen_port=None, tmp_dir='data'):
    path = None
    try:
        if chosen_port is None:
            chosen_port = choose_serial_port()

        path = create_dumper_file(chosen_port, tmp_dir=tmp_dir)
        run_reader(chosen_port, Dumper(path))
    except ValueError as ex:
        print(ex)
        print("Quit.")
    except KeyboardInterrupt as ex:
        print(ex)
        print("Force quit.")
    finally:
        return path

if __name__ == "__main__":
    try:
        filename = dumper_main()
        if filename:
            print('serial data written into ' + filename)
    except serial.SerialException as e:
        print("Cannot start serial connection: {0}".format(e))
        sys.exit(1)
