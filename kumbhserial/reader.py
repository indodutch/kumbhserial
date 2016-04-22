import serial
import threading
import time
from .helpers import text_in, insert_timestamp


class SerialReader(threading.Thread):

    WAIT_FOR_DEVICE_TIMEOUT = 12

    def __init__(self, port, appender, heartbeat=True, terminator=b'\r',
                 insert_timestamp_at=(b'>', b'<')):
        super().__init__()
        self.comm = serial.Serial(port, 921600, timeout=1)
        self.port = port
        self.is_done = False
        self.appender = appender
        self.receive_until = time.time()
        if heartbeat:
            self.heartbeat = Heartbeat(self.comm)
        else:
            self.heartbeat = None
        self.exception = None
        self.terminator = terminator
        self.insert_timestamp_at = insert_timestamp_at

    def start(self):
        super().start()
        if self.heartbeat:
            self.heartbeat.start()

    def run(self):
        print('started logger')
        try:
            while not self.is_done or time.time() < self.receive_until:
                data = self.comm.read_until(terminator=self.terminator)
                for token in self.insert_timestamp_at:
                    data = insert_timestamp(data, token)
                self.appender.append(data)
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
            self.receive_until = (time.time() +
                                  SerialReader.WAIT_FOR_DEVICE_TIMEOUT)
            if self.heartbeat:
                self.heartbeat.done()


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


def run_reader(port, appender, **kwargs):
    print('Reading ' + port + '. Type q or quit to quit.')
    reader = SerialReader(port, appender, **kwargs)
    print('Starting {0}...'.format(port))
    reader.start()
    try:
        while reader.exception is None:
            text_in()  # waiting for user input
    except (ValueError, KeyboardInterrupt):
        print('Stopping {0}...'.format(reader.port))
    finally:
        reader.done()
        reader.join(SerialReader.WAIT_FOR_DEVICE_TIMEOUT + 1)
        if reader.exception:
            print('Failed to communicate: {0}'.format(reader.exception))
        print('Stopped {0}.'.format(reader.port))
