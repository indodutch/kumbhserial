# Indo-Dutch Kumbh Mela experiment serial device reader
#
# Copyright 2015 Zoltan Beck, Netherlands eScience Center, and
#                University of Amsterdam
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import serial
import threading
import time
from .helpers import text_in, insert_timestamp


class SerialReader(threading.Thread):

    """
    Reads a serial device, as provided in the Kumbh Mela project.
    """

    def __init__(self, port, appender, writer=None, terminator=b'\r',
                 insert_timestamp_at=(b'>', b'<'), baud_rate=921600,
                 wait_time=12):
        """
        Starts a serial port reader.
        :param port: serial port name
        :param appender: appender to write lines to
        :param writer: threading.Thread that takes a serial port as initial
            parameter. If it is None, no data will be written.
        :param terminator: end-of-line terminator. It will not read beyond this
            terminator. Pass None to read
        :param insert_timestamp_at:
        :param baud_rate:
        :return:
        """
        super().__init__()
        self.comm = serial.Serial(port, baud_rate, timeout=1)
        self.port = port
        self.is_done = False
        self.appender = appender
        self.receive_until = time.time()
        if writer is not None:
            self.writer = writer(self.comm)
        else:
            self.writer = None
        self.exception = None
        self.terminator = terminator
        self.insert_timestamp_at = insert_timestamp_at
        self.wait_time = wait_time

    def start(self):
        super().start()
        if self.writer:
            self.writer.start()

    def read(self):
        data = self.comm.read_until(terminator=self.terminator)
        for token in self.insert_timestamp_at:
            data = insert_timestamp(data, token)
        self.appender.append(data)

    def run(self):
        print('started logger')
        try:
            while not self.is_done or time.time() < self.receive_until:
                self.read()
            print('read stopped')
        except Exception as ex:
            self.exception = ex
            print('read or write failed, press ENTER to quit.')

    def join(self, timeout=None):
        try:
            super().join(timeout=timeout)
        finally:
            self.appender.done()

    def done(self):
        if not self.is_done:
            self.is_done = True
            self.receive_until = (time.time() + self.wait_time)
            if self.writer:
                self.writer.done()


class Heartbeat(threading.Thread):
    def __init__(self, comm, sleep=1):
        super().__init__()
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


def read_file(filename, appender, terminator=b'\r'):
    buffer = b''
    buffer_size = 1024
    with open(filename, 'rb') as f:
        terminator_idx = 0
        while terminator_idx != -1:
            new_buffer = b'i'
            while terminator not in new_buffer and len(new_buffer) > 0:
                new_buffer = f.read(buffer_size)
                buffer += new_buffer

            terminator_idx = buffer.find(terminator)
            appender.append(buffer[:terminator_idx + len(terminator)])
            buffer = buffer[terminator_idx + len(terminator):]

        appender.append(buffer)
        appender.done()


def run_reader(port, appender, writer=None, **kwargs):
    print('Reading ' + port + '. Type q or quit to quit.')
    if writer is None:
        writer = Heartbeat
    reader = SerialReader(port, appender, writer=writer, **kwargs)
    print('Starting {0}...'.format(port))
    reader.start()
    try:
        while reader.exception is None:
            text_in()  # waiting for user input
    except (ValueError, KeyboardInterrupt):
        print('Stopping {0}... WAIT {1} SECONDS!'
              .format(reader.port, reader.wait_time + 3))
    finally:
        reader.done()
        reader.join(reader.wait_time + 1)
        if reader.exception:
            print('Failed to communicate: {0}'.format(reader.exception))
        print('Stopped {0}.'.format(reader.port))
