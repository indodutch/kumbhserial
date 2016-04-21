# -*- coding: utf-8 -*-
"""
Created on Mon Apr 04 14:55:32 2016

@author: Zoli
"""

import serial
import time
import sys
import threading
import base64
from queue import Queue
from .ports import choose_serial_port
from .appenders import run_reader


class KumbhMelaInterpreter(threading.Thread):
    WAIT_FOR_FINISH_READ = 2

    def __init__(self):
        super(KumbhMelaInterpreter, self).__init__()
        self.is_done = False
        self.current_data = None
        self.error_cnt = 0
        self.file_cnt = 0
        self.read_till = time.time()
        self.read_queue = Queue()
        self.partial_line = None

    def append(self, data):
        if len(data) == 0:
            # nothing arrived within the timeout
            return

        if self.partial_line is not None:
            data = self.partial_line + data
            self.partial_line = None

        if data[-1] != ord(b'\r'):
            # an incomplete line arrived before the timeout hit in
            self.partial_line = data
        else:
            data = data.strip()
#            if len(line) < 1:
#                #empty line somehow...
#                print('empty line')
#                continue
        self.read_queue.put(data)

    def save_data(self):
        if self.current_data:
            if not self.current_data.OK:
                self.error_cnt += 1
                print('%d: %d' % (self.error_cnt, self.current_data.errcode))
#                print('\n'.join(self.serial_buffer[:self.serial_buffer_read_index]))
            self.current_data.save('data/%s_%s-%d.dat' % (self.port,
                                    time.strftime("%Y%m%d-%H%M%S"), self.file_cnt))
            self.file_cnt += 1
            self.current_data = None

    def run(self):
        while not self.is_done or time.time() < self.read_till:
            line = self.read_queue.get()
            if len(line) == 1:
                continue
            if line[0] == '>':
                self.save_data()
                self.current_data = DataRead(line[1:])
            # maximum line address is 279620 with full 4MB data
            elif ((line[0] in ['0', '1', '2']) and
                  (self.current_data is not None)):
                if len(line) != 29:
                    # print(len(line), line)
                    self.handle_error(10)
                else:
                    try:
                        line_id = int(line[:6])
                        self.current_data.add_data(line_id, line[6:])
                    except ValueError:
                        self.handle_error(11)
            elif line[0] == '<':
                self.save_data()
            else:
                self.handle_error(12)
        print('read stopped')
        self.save_data()

    def handle_error(self, errcode=0):
        if self.current_data:
            self.current_data.error(errcode)
            self.save_data()

    def done(self):
        if not self.is_done:
            self.read_till = self.WAIT_FOR_FINISH_READ
            self.is_done = True


class DataRead(object):
    def __init__(self, device_id):
        self.id = device_id
        self.data = [[], []]
        self.system = self.data[0]
        self.detections = self.data[1]
        self.errcode = -1

    @property
    def OK(self):
        return self.errcode != -1

    def error(self, errcode=0):
        self.errcode = errcode

    def __str__(self):
        if self.OK:
            text = 'device_id: %s\nsystem:\n' % (self.id,)
            for number, line in enumerate(self.system):
                text += '%d:\t%s\n' % (number, line)
            text += '\ndetections:\n'
            for number, line in enumerate(self.detections):
                text += '%d:\t%s\n' % (number, line)
            return text
        else:
            return 'Corrupted reading!!\n\n'

    def save(self, fname):
        with open(fname+'s', 'wb') as f:
            for line in self.system:
                f.write(line)

        with open(fname+'d', 'wb') as f:
            for line in self.detections:
                f.write(line)

    def add_data(self, line_id, data):
        if data[0] == ':':
            is_detection = True
        elif data[0] == '-':
            is_detection = False
        else:
            self.error(1)
            return

        if 0 < len(self.data[is_detection]) < line_id:
            self.error(2)
            return

        try:
            ddata = base64.b64decode(data[1:]+'==')
        except TypeError:
            self.error(3)
        else:
            if sum(bytearray(ddata)) % 256 != 0:
                self.error(4)

            while line_id > len(self.data[is_detection]) - 1:
                self.data[is_detection].append([chr(255)]*15)

            self.data[is_detection][line_id] = ddata[1:]


def run_logger(port):
    logger = KumbhMelaInterpreter()
    logger.start()
    run_reader(port, logger)
    logger.done()
    logger.join(KumbhMelaInterpreter.WAIT_FOR_FINISH_READ + 1)


def main():
    try:
        chosen_port = choose_serial_port()
        run_logger(chosen_port)
    except ValueError:
        print("Quit.")
    except KeyboardInterrupt:
        print("Force quit.")
    except serial.SerialException as e:
        print("Cannot start serial connection: {0}".format(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
