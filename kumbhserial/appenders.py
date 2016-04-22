# -*- coding: utf-8 -*-
import json
import threading
import queue
from .helpers import output_filename


class Dumper(object):
    def __init__(self, path):
        self.file = open(path, 'wb')

    def append(self, data):
        if len(data) > 0 and self.file:
            self.file.write(data)
            self.file.flush()

    def done(self):
        self.file.close()
        self.file = None


class Duplicator(object):
    def __init__(self, appenders):
        self.appenders = appenders

    def append(self, data):
        for a in self.appenders:
            a.append(data)

    def done(self):
        for a in self.appenders:
            a.done()


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


class ThreadBuffer(threading.Thread):
    def __init__(self, appender, **kwargs):
        self.appender = appender
        self.queue = queue.Queue()
        self.is_done = False
        super().__init__(**kwargs)
        self.start()

    def append(self, data):
        self.queue.put(data)

    def run(self):
        while not self.is_done:
            try:
                data = self.queue.get(timeout=1)
                self.appender.append(data)
            except queue.Empty:
                pass

    def join(self, **kwargs):
        self.done()
        try:
            super().join(**kwargs)
        finally:
            self.appender.done()

    def done(self):
        if not self.is_done:
            self.is_done = True
            self.join()


def create_dumper_file(port, output_dir='data'):
    port_id = port.split('/')[-1]
    return output_filename(output_dir, 'dump-' + port_id, 'txt')
