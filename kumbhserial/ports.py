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
Listing and selecting serial port devices.
"""

import sys
import glob
import serial
from .helpers import text_in, select_value_from_list


def serial_ports():
    """
    Lists serial port names. It may take some time: for each of the systems
    serial ports it checks whether it is accessible for the current user.

    :raises EnvironmentError: unsupported operating system or platform.
    :return: A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def choose_serial_port(preamble=None):
    """
    Choose a serial port with a terminal prompt.
    :param preamble: object to print before the prompt.
    :return: serial port device name
    :raise ValueError: user quit by typing quit command.
    :raise KeyboardInterrupt: user quit by sending an interrupt.
    """
    while True:
        ports = serial_ports()

        if preamble is not None:
            print(preamble)
        if len(ports) > 0:
            print('{0}\nSerial port '
                  '(leave empty to reload, type q or quit to quit):'
                  .format('\n'.join(['{0}: {1}'.format(i, l)
                                     for i, l in enumerate(ports)])))

            text = text_in()
            if len(text) > 0:
                try:
                    return select_value_from_list(text, ports)
                except (ValueError, IndexError):
                    print('ERROR: Given port not in the list. Try again.')
        else:
            print('No serial device detected, please plug in device.\n'
                  'Press ENTER to reload, type q or quit to quit).')
            text_in()


def resolve_serial_port(name):
    """
    Resolve a literal serial port from given string.
    An input of a serial port name will try to be matched to available serial
    ports. An input number string is taken as the index of serial ports.
    None will be returned as None.
    :param name: string containing a serial port name or an index number. May
        be None.
    :return: exact serial port name or None.
    :raises ValueError: if given string cannot be translated to a serial port.
    """
    if name is None:
        return None
    ports = serial_ports()
    try:
        return select_value_from_list(name, ports)
    except (ValueError, IndexError):
        port_strs = ['{0}: {1}'.format(i, p) for i, p in enumerate(ports)]
        raise ValueError('Device number invalid, choose from:\n* {0}'.format(
            '\n* '.join(port_strs)))


if __name__ == '__main__':
    print(serial_ports())
