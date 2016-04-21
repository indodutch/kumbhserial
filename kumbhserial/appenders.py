# -*- coding: utf-8 -*-
import json
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
