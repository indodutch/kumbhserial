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
Facilities to read out the Kumbh Mela GPS devices.
"""

import threading
import serial
from .reader import SerialReader


class GpsReaderThread(threading.Thread):
    """
    Thread to read out a GPS device
    """
    def __init__(self, port, appender, clear=True, **kwargs):
        super().__init__()
        self.interpreter = GpsInterpreter(port, appender)
        self.reader = SerialReader(port, self.interpreter, wait_time=1,
                                   baud_rate=115200, terminator=b'#',
                                   insert_timestamp_at=(), **kwargs)
        self.clear = clear

    def run(self):
        try:
            writer = GpsWriter(self.reader.comm)
            writer.start_transfer()
            print('Reading <{0}>...'.format(self.reader.port))
            while (not self.interpreter.is_done and
                   self.interpreter.num_empty < 3):
                self.reader.read()

            if self.interpreter.has_error():
                print('Error parsing {0}'.format(self.interpreter))
            elif self.interpreter.num_records == 0:
                print('Device <{0}> is empty, set to CHARGE mode, or not a'
                      ' GPS device.'.format(self.reader.port))
            elif self.clear:
                writer.clear()
                print("Cleared {0}. Done.".format(self.interpreter))
            else:
                print('Done reading {0}.'.format(self.interpreter))
        except serial.SerialException as ex:
            print('Failed to read serial device {0}'
                  .format(self.interpreter, ex))
        finally:
            self.reader.done()
            if not self.interpreter.is_done:
                self.interpreter.done()


class GpsWriter(object):
    """
    GPS commands.
    """
    def __init__(self, comm):
        self.comm = comm

    def start_transfer(self):
        self.comm.write(b'OpenT')

    def clear(self):
        self.comm.write(b'clearM')


class GpsInterpreter(object):
    """
    Interprets the output of a GPS serial device and outputs a dict.

    Records num_records as the number of valid records, and num_empty
    as the number of consecutive empty data strings received. If num_empty is
    large, most probably the GPS device will not send any output at all. If the
    end of the data stream is reached, according to the device data, the
    interpreter will set is_done to True. The current_id is known as soon as
    valid data comes in, which contains the device id.
    """
    def __init__(self, port, appender):
        self.appender = appender
        self.errors = []
        self.is_done = False
        self.num_empty = 0
        self.num_records = 0
        self.current_id = None
        self.port = port

    def has_error(self):
        return len(self.errors) > 0

    def append(self, data):
        if len(data) == 0:
            self.num_empty += 1
            return

        self.num_empty = 0
        self.num_records += 1
        data = str(data, encoding='ascii')

        if data == '@':
            self.done()
        if not data.endswith('#'):
            self.errors.append('cannot read end of line \'#\': ' + data)
            return
        if not data.startswith('$'):
            self.errors.append('Cannot read start of line \'$\': ' + data)
            return
        # example data record:
        # $TI010,230416125520,2310.6876N,07543.6625E,000.00,029.87,14,1#
        str_data = str(data[1:-1], encoding='ascii')
        try:
            cols = str_data.split(',')
            self.current_id = cols[0]
            self.appender.append({
                'deviceId': self.current_id,
                'date': '20' + cols[1][4:6] +
                        '-' + cols[1][2:4] +
                        '-' + cols[1][0:2],
                'time': cols[1][6:8] +
                        ':' + cols[1][8:10] +
                        ':' + cols[1][10:12],
                'coordNorthSouth': cols[2][-1:],
                'latitude': float(cols[2][:-1]) / 100.,
                'coordEastWest': cols[3][-1:],
                'longitude': float(cols[3][:-1]) / 100.,
                'speed': float(cols[4]),
                'direction': float(cols[5]),
                'numberOfSatellites': int(cols[6]),
                'line': int(cols[7]),
            })
        except IndexError as ex:
            self.errors.append(
                'expected 8 columns of data (record #{0}): {1}: {2}'
                .format(self.num_records, ex, data))
        except ValueError as ex:
            self.errors.append(
                'data types do not match (record #{0}): {1}: {2}'
                .format(self.num_records, ex, data))

    def __str__(self):
        ret = 'GPS <device: {0}>'.format(self.port)
        if self.current_id:
            ret += ' ' + self.current_id
        ret += ' (' + str(self.num_records) + ' records)'
        if self.has_error():
            ret += (' FAILED: ' +
                    ''.join('\n* error: {0}'.format(e) for e in self.errors))
        return ret

    def done(self):
        if not self.is_done:
            self.is_done = True
            self.appender.done()
