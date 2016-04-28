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

from nose.tools import assert_equals, assert_list_equal

from kumbhserial.interpreter import TrackerEntrySet, TrackerInterpreter


class MockAppender():
    def __init__(self, mock_data=()):
        self.mock_data = mock_data
        self.i = 0
        self.is_done = False

    def append(self, data):
        assert_equals(self.mock_data[self.i], data)
        self.i += 1

    def done(self):
        assert_equals(self.i, len(self.mock_data))


def test_empty_tracker_interpreter():
    out = TrackerEntrySet(0, '2016-04-23T22:59:00.0000')
    out.detections = [{'line': 0, 'type': 0, 'id': 23, 'rssi': -47},
                      {'line': 0, 'type': 0, 'id': 23, 'rssi': -35},
                      {'line': 0, 'type': 0, 'id': 23, 'rssi': -35},
                      {'line': 0, 'type': 0, 'id': 23, 'rssi': -35},
                      {'line': 0, 'type': 0, 'id': 23, 'rssi': -35},
                      {'line': 0, 'type': 0, 'id': 23, 'rssi': -35}]
    out.system = [{'line': 1, 'auth': 12481, 'time': 4014330, 'density': 2,
                   'rtc': 4014325, 'reset': 1, 'state': 1, 'detection': 0}]
    out.end_time = '2016-04-23T23:00:00.0000'

    parser = TrackerInterpreter(MockAppender((out,)))
    parser.append(b'some junk\r')
    parser.append(b'\n>%2016-04-23T22:59:00.0000%0\r')
    parser.append(b'\n000000-RVhQRVJJTUVOVF9EQVRBAA\r')
    parser.append(b'\n000001-IQL6QD0AAAAwwQMAAPVAPQ\n')
    parser.append(b'\n007049-/////////////////////w\r')
    parser.append(b'\n000000:XxsBcPAXDwFw8BcPAXDwFw\r')
    parser.append(b'\n000554://////////////////////\r')
    parser.append(b'\n<%2016-04-23T23:00:00.0000%0\r')
    parser.append(b'some junk\r')
    parser.done()


def test_tracker_entryset():
    tracker = TrackerEntrySet(0, None)
    # invalid data explicitly mentioned
    tracker.add_system(0, b'RVhQRVJJTUVOVF9EQVRBAA')
    assert_equals([], tracker.system)
    tracker.add_system(400, b'//////////////////////')
    assert_equals([], tracker.system)
    tracker.add_system(1, b'IQL6QD0AAAAwwQMAAPVAPQ')
    assert_equals({'line': 1, 'auth': 12481, 'time': 4014330, 'density': 2,
                   'rtc': 4014325, 'reset': 1, 'state': 1, 'detection': 0},
                  tracker.system[0])

    tracker.add_detection(0, b'/////////////////////w')
    assert_equals([], tracker.detections)
    tracker.add_detection(0, b'XxsBcPAXDwFw8BcPAXDwFw')
    assert_list_equal([{'line': 0, 'type': 0, 'id': 23, 'rssi': -47},
                       {'line': 0, 'type': 0, 'id': 23, 'rssi': -35},
                       {'line': 0, 'type': 0, 'id': 23, 'rssi': -35},
                       {'line': 0, 'type': 0, 'id': 23, 'rssi': -35},
                       {'line': 0, 'type': 0, 'id': 23, 'rssi': -35},
                       {'line': 0, 'type': 0, 'id': 23, 'rssi': -35}],
                      tracker.detections)

