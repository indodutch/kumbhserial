import sys

from kumbhserial.reader import read_file
from .helpers import timestamp
from .appenders import JsonListAppender, Dumper


class SnifferInterpreter(object):
    def __init__(self, appender):
        self.appender = appender
        self.line_number = 0

    def append(self, line):
        line = line.strip()
        if len(line) == 0:
            return
        if b',' in line:
            elements = [part.strip() for part in line.split(b',')]
            sniffed = {
                'rtc': int(elements[0]),
                'time': int(elements[1]),
                'state': str(elements[2], encoding='ascii'),
                'id': int(elements[3]),
                'density': int(elements[4]),
                'auth': int(elements[5], base=16)
            }
        else:
            sniffed = {
                'rtc': int(line),
            }
        sniffed['timestamp'] = timestamp()
        sniffed['line'] = self.line_number
        self.line_number += 1

        self.appender.append(sniffed)

    def done(self):
        self.appender.done()


if __name__ == '__main__':
    parser = SnifferInterpreter(JsonListAppender(Dumper(sys.argv[2])))
    read_file(sys.argv[1], parser)
