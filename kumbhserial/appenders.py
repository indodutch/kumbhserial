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

""" Pipe-like appenders, to dump data with different methods and formats. """

import json
import threading
import queue


class Dumper(object):
    """
    Dumps bytes data to file.
    """
    def __init__(self, path, flush=True):
        """
        :param path: file path to write to.
        :param flush: flush to file after writing. Slower but safer.
        """""
        self.file = open(path, 'wb')
        self.flush = flush

    def append(self, data):
        if len(data) > 0 and self.file:
            self.file.write(data)
            if self.flush:
                self.file.flush()

    def done(self):
        self.file.close()
        self.file = None


class Duplicator(object):
    """
    Send the same incoming data to a sequence of appenders.
    """
    def __init__(self, appenders):
        self.appenders = appenders

    def append(self, data):
        for a in self.appenders:
            a.append(data)

    def done(self):
        for a in self.appenders:
            a.done()


class RawPrinter(object):
    """
    Print incoming data to console.
    """
    def append(self, data):
        print(data)

    def done(self):
        pass


class JsonListAppender(object):
    """
    Convert incoming data to a list of json objects. Each call to append will
    add one JSON object to a JSON list.
    """
    def __init__(self, appender):
        self.appender = appender
        self.first = True
        self.appender.append(b'[')

    def append(self, data):
        if self.first:
            self.first = False
        else:
            self.appender.append(b',')

        self.appender.append(bytes(json.dumps(data, separators=(',', ':')),
                                   encoding='ascii'))

    def done(self):
        self.appender.append(b']')
        self.appender.done()


class ThreadBuffer(threading.Thread):
    """
    Put a thread between the sender and the receiver, so that these can act
    concurrently. This is helpful if both the sender and receiver do
    independent I/O operations.
    """
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
                pass  # no input yet, check if is_done

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
