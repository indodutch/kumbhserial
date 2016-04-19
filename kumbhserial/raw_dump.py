# -*- coding: utf-8 -*-
"""
Created on Mon Apr 04 14:55:32 2016

@author: Zoli
"""

from .reader import run_reader
import serial
import time
import sys
import os
from .ports import choose_serial_port


class Dumper(object):
    def __init__(self, path):
        self.file = open(path, 'wb')

    def append(self, data):
        if len(data) > 0:
            self.file.write(data)
            self.file.flush()

    def done(self):
        self.file.close()


class RawPrinter(object):
    def append(self, data):
        print(data)

    def done(self):
        pass


def create_dumper_file(port, tmp_dir='data'):
    port_id = port.split('/')[-1]
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    return os.path.join(tmp_dir, 'dump-{0}{1}.txt'.format(
        port_id, time.strftime("%Y%m%d-%H%M%S")))


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
