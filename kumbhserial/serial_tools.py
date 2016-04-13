# -*- coding: utf-8 -*-
"""
Created on Thu Apr 07 17:04:39 2016

@author: Zoli
"""

import sys
import glob
import serial


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
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


def wait_for_user_quit(quit_commands=('q', 'quit')):
    while True:
        text_in(quit_commands)


def text_in(quit_commands=('q', 'quit')):
    try:
        text = sys.stdin.readline().strip().lower()
        if text in quit_commands:
            raise ValueError('Quit')
        return text
    except KeyboardInterrupt:
        raise ValueError('Quit')


def choose_serial_port():
    while True:
        ports = serial_ports()

        if len(ports) > 0:
            print('Pick a serial port (type q or quit to quit):%s' % (' '.join(
                ['\n%d: %s' % (i, l) for i, l in enumerate(ports)]),))

            text = text_in()
            if text in [p.lower() for p in ports]:
                return ports[[p.lower() for p in ports].index(text)]

            try:
                return ports[int(text)]
            except (ValueError, IndexError):
                print('Given port not in the list. Try again.')
        else:
            print('No serial device detected, please plug in bracelet.\n'
                  'Press ENTER to retry, type q or quit to quit).')
            text_in()

if __name__ == '__main__':
    print(serial_ports())