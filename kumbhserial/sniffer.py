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

"""
Handle the Salland Electronics sniffer node.
"""

from .helpers import timestamp


class SnifferInterpreter(object):
    """
    Interprets the output of the Salland Electronics sniffer node. Accepts
    bytes and sends dict objects to given appender with the output data.
    """
    def __init__(self, appender):
        self.appender = appender
        self.line_number = 0

    def append(self, line):
        """
        Parse bytes data and convert it to a dict.
        :param line: a single record of bytes data.
        """
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
        """
        Mark the interpreter and its appender as done.
        """
        self.appender.done()


if __name__ == '__main__':
    import sys
    from .appenders import JsonListAppender, Dumper
    from .reader import read_file

    parser = SnifferInterpreter(JsonListAppender(Dumper(sys.argv[2])))
    read_file(sys.argv[1], parser)
