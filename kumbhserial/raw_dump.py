# -*- coding: utf-8 -*-
"""
Created on Mon Apr 04 14:55:32 2016

@author: Zoli
"""
import json

from kumbhserial.helpers import output_filename
from .reader import run_reader
import serial
import sys
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


class JsonListAppender(object):
    def __init__(self, appender):
        self.appender = appender
        self.first = True
        self.appender.append(b'[')

    def append(self, data):
        if self.first:
            self.first = False
        else:
            self.appender.append(b',')

        self.appender.append(bytes(json.dumps(data), encoding='ascii'))

    def done(self):
        self.appender.append(b']')
        self.appender.done()


def create_dumper_file(port, tmp_dir='data'):
    port_id = port.split('/')[-1]
    return output_filename(tmp_dir, 'dump-' + port_id, 'txt')


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
