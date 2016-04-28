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
Parser and interpreter of the Kumbh Mela lanyard devices.
"""

import base64
from .helpers import timestamp


class TrackerInterpreter(object):
    """
    Parses the raw data from the lanyard devices.
    """
    def __init__(self, appender):
        self.appender = appender
        self.current_entries = None

    def append(self, line):
        # if line[0] != '\n':
        # skipping lines not part of the well-defined stream
        # return

        line = bytes(line.strip())

        if len(line) == 0:
            return
        if line.startswith(b'>'):
            if self.current_entries is not None:
                self.log(
                    error='Starting new device log when the old one was not '
                          'finished')
            parts = line.split(b'%')
            if len(parts) == 3:
                time = str(parts[1], encoding='ascii')
                device_id = parts[2]
            else:
                time = timestamp()
                device_id = line[1:]

            self.current_entries = TrackerEntrySet(int(device_id), time)
            return
        elif self.current_entries is None:
            # skip lines not generated by a node
            return

        # maximum line address is 279620 with full 4MB data
        if (line.startswith(b'0') or line.startswith(b'1') or
                line.startswith(b'2')):
            if len(line) != 29:
                self.log(error=b'Device log line not length 29: ' + line)
                return
            else:
                try:
                    line_id = int(line[:6])
                    if line[6:].startswith(b':'):
                        self.current_entries.add_detection(line_id, line[7:])
                    elif line[6:].startswith(b'-'):
                        self.current_entries.add_system(line_id, line[7:])
                    else:
                        self.log(
                            error=b'Invalid device log line format: ' + line)
                except ValueError:
                    self.log(error=b'Invalid device log line format: ' + line)
        elif line.startswith(b'<'):
            parts = line.split(b'%')
            if len(parts) == 3:
                self.current_entries.end_time = str(parts[1], encoding='ascii')
                device_id = parts[2]
            else:
                self.current_entries.end_time = timestamp()
                device_id = line[1:]

            if int(device_id) == self.current_entries.device_id:
                self.log()
            else:
                self.log(
                    error=b'Started with device ID {0} and ended with device '
                    b'ID {1}'.format(self.current_entries.device_id,
                                     line[1:]))
        else:
            self.log(error=b'Unknown line type: ' + line)

    def log(self, error=None):
        if self.current_entries is not None:
            if error is not None:
                self.current_entries.error = error
            self.appender.append(self.current_entries)
            self.current_entries = None

    def done(self):
        self.log()
        self.appender.done()


class TrackerEntrySet(object):
    """
    Interprets individual records of the lanyard devices. If their was a
    problem with the device output, the error property will be set.
     """
    separator = b'/' * 21

    def __init__(self, device_id, time):
        self.device_id = device_id
        self.time = time
        self.end_time = None
        self._error = None
        self.system = []
        self.detections = []

    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, error):
        print('ERROR: reading device {0} failed: {1}'
              .format(self.device_id, error))
        self._error = error

    def decode(self, b64data):
        """
        Decode the base 64 data and check the checksum. It will ignore the

        :param b64data: 22 bytes of base64 encoded binary data.
        :return: decoded bytes.
        """
        # The last line of a detection log has the last (one or more)
        # 16bit samples set with all bits 1, in base 64 representation
        #  the last two characters are // as a result and the
        # character preceding it must be f, v or /.
        if b64data.startswith(TrackerEntrySet.separator):
            raise ValueError('separator')

        try:
            binary_data = bytearray(base64.b64decode(b64data + b'=='))
        except TypeError:
            self.error = 'data is not in the correct format'
        else:
            if binary_data == b'EXPERIMENT_DATA\x00':
                raise ValueError('experiment data')
            if sum(binary_data) % 256 != 0:
                self.error = 'data checksum {0} invalid: {1}'.format(
                    sum(binary_data) % 256, b64data)

            return binary_data

    def add_system(self, line_id, b64data):
        try:
            hex_data = self.decode(b64data)
        except ValueError:
            return
        self.system.append({
            'line': line_id,
            # system.lrc = 0x12
            # 12000000 00000000 00000000 00000000
            # ignore, only a checksum
            # 'lrc': hex_data[0],
            # system.density = 0x12
            # 00120000 00000000 00000000 00000000
            'density': hex_data[1],
            # system.time = 0x12345678ABCDEF
            # 0000EFCD AB785634 00000000 00000000
            'time': (hex_data[2] +
                     (hex_data[3] << 8) +
                     (hex_data[4] << 16) +
                     (hex_data[5] << 24) +
                     (hex_data[6] << 32) +
                     (hex_data[7] << 36)),
            # system.auth = 0x1234
            # 00000000 00000000 34120000 00000000
            'auth': (hex_data[8] << 8) + hex_data[9],
            # system.reset = 1
            # 00000000 00000000 00000100 00000000
            'reset': hex_data[10] & 0x1,
            # system.state = 3
            # 00000000 00000000 00000600 00000000
            # system.state = 2
            # 00000000 00000000 00000400 00000000
            'state': (hex_data[10] & 0x6) >> 1,
            # system.rtc = 0x123456
            # 00000000 00000000 00000000 00563412
            'rtc': (hex_data[13] +
                    (hex_data[14] << 8) +
                    (hex_data[15] << 16)),
            # system.detection = 0x123456 (if you left shift this by three you
            #                              get 91A2B0)
            # 00000000 00000000 0000B0A2 91000000
            'detection': ((hex_data[10] & ~0x7) +
                          (hex_data[11] << 8) +
                          (hex_data[12] << 16)) >> 3,
        })

    def add_detection(self, line_id, b64data):
        # detect.lrc = 0x12
        try:
            hex_data = self.decode(b64data)[1:]
        except ValueError:
            return
        oct_data = []
        for h in hex_data:
            oct_data.append((h & 0xf0) >> 4)
            oct_data.append(h & 0x0f)

        # 12000000 00000000 00000000 00000000
        #
        # >put the same 20 bits of data in detect (count 0, 1, 2, 3, 4, 5)
        #
        # data = 0x12345
        # 00123450 00000000 00000000 00000000
        #
        # data = 0x12345
        # 00000001 23450000 00000000 00000000
        #
        # etc...
        for i in range(0, 30, 5):
            if (oct_data[i] &
                    oct_data[i + 1] &
                    oct_data[i + 2] &
                    oct_data[i + 3] &
                    oct_data[i + 4]) == 0xf:
                break
            self.detections.append({
                'line': line_id,
                # type = 3
                # C0000
                #
                # type = 1
                # 40000
                'type': (oct_data[i] >> 2),
                # rssi = 21 (20 + 1)
                # 01000
                #
                # rssi = 82 (20 + 0x3E)
                # 3E000
                'rssi': -(20 + (((oct_data[i] << 4) +
                                 oct_data[i + 1]) & 0x3f)),
                # id = 0xABC
                # 00ABC
                'id': ((oct_data[i + 2] << 8) +
                       (oct_data[i + 3] << 4) +
                       oct_data[i + 4])
            })

    def __str__(self):
        ret = 'Device({0} detections, {1} system, {2})'.format(
                len(self.detections), len(self.system), self.time)
        if self.error is not None:
            ret += ' failed: {0}'.format(self.error)
        return ret

    def __repr__(self):
        if self.error is None:
            text = 'device_id: {0} at time {1}\nsystem:\n'.format(
                self.device_id, self.time)
            for line in self.system:
                text += '{0}\n'.format([(key, line[key])
                                        for key in sorted(line.keys())])
            text += '\ndetections:\n'
            for line in self.detections:
                text += '{0}\n'.format([(key, line[key])
                                        for key in sorted(line.keys())])
            return text
        else:
            return 'Corrupted reading: error {0}\n\n'.format(self.error)

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __hash__(self):
        return hash((self.device_id, self.time))


class TrackerEntrySetAppender(object):
    """
    Converts a TrackerEntrySet to a single dict without data duplication.
    """
    def __init__(self, appender):
        self.appender = appender

    def append(self, entry_set):
        entry_dict = {
            'id': entry_set.device_id,
            'time': entry_set.time,
            'endTime': entry_set.end_time,
            'detections': entry_set.detections,
            'system': entry_set.detections,
        }
        if entry_set.error is not None:
            entry_dict['error'] = entry_set.error

        self.appender.append(entry_dict)

    def done(self):
        self.appender.done()


class SeparatedTrackerEntrySetJsonConverter(object):
    """
    Converts a TrackerEntrySet to a detections and system dict. The output
    dict does not have any nested dicts or lists and has some data duplication
    (id, time, endTime).
    """
    def __init__(self, appender_detections, appender_system):
        self.appender_detections = appender_detections
        self.appender_system = appender_system

    def append(self, entry_set):
        base = {'deviceId': entry_set.device_id,
                'time': entry_set.time,
                'endTime': entry_set.end_time}
        if entry_set.error:
            base['error'] = entry_set.error

        for d in entry_set.detections:
            a = base.copy()
            a.update(d)
            self.appender_detections.append(a)

        for s in entry_set.system:
            a = base.copy()
            a.update(s)
            self.appender_system.append(a)

    def done(self):
        self.appender_system.done()
        self.appender_detections.done()


if __name__ == '__main__':
    import sys
    from .appenders import JsonListAppender, Dumper
    from .reader import read_file

    parser = TrackerInterpreter(
        SeparatedTrackerEntrySetJsonConverter(
            JsonListAppender(Dumper(sys.argv[2])),
            JsonListAppender(Dumper(sys.argv[3]))))
    read_file(sys.argv[1], parser)
