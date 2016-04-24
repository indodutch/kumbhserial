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


class GpsWriter(object):
    def __init__(self, comm):
        self.comm = comm

    def start_transfer(self):
        self.comm.write(b'OpenT')

    def clear(self):
        self.comm.write(b'clearM')

    def done(self):
        pass


class GpsInterpreter(object):
    def __init__(self, appender):
        self.appender = appender
        self.error = None
        self.is_done = False
        self.num_empty = 0
        self.num_records = 0

    def append(self, data):
        if len(data) == 0:
            self.num_empty += 1
        self.num_empty = 0
        self.num_records += 1
        if data == b'@':
            self.done()
        if not data.endswith(b'#'):
            self.error = 'Cannot read end of line #'
            return
        if not data.startswith(b'$'):
            self.error = 'Cannot read start of line $'
            return
        # example data record:
        # $TI010,230416125520,2310.6876N,07543.6625E,000.00,029.87,14,1#
        cols = data[1:-1].split(b',')
        self.appender.append({
            'deviceId': str(cols[0], encoding='ascii'),
            'date': str(b'20' + cols[1][4:6] +
                        b'-' + cols[1][2:4] +
                        b'-' + cols[1][0:2], encoding='ascii'),
            'time': str(cols[1][6:8] +
                        b':' + cols[1][8:10] +
                        b':' + cols[1][10:12], encoding='ascii'),
            'coordNorthSouth': str(cols[2][-1:], encoding='ascii'),
            'latitude': float(cols[2][:-1]) / 100.,
            'coordEastWest': str(cols[3][-1:], encoding='ascii'),
            'longitude': float(cols[3][:-1]) / 100.,
            'speed': float(cols[4]),
            'direction': float(cols[5]),
            'numberOfSatellites': int(cols[6]),
            'line': int(cols[7]),
        })

    def done(self):
        if not self.is_done:
            self.is_done = True
            self.appender.done()
