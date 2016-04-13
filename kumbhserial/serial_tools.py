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


def choose_serial_port():
    quit_commands = ('q', 'quit')

    while True:
        ports = serial_ports()
        if len(ports) == 0:
            print('No serial device detected, please plug in bracelet.')
            if sys.stdin.readline().strip().lower() in quit_commands:
                raise ValueError("Quit")
        print('Pick a serial port:%s' % (' '.join(
            ['\n%d: %s' % (i, l) for i, l in enumerate(ports)]),))
        text_in = sys.stdin.readline().strip().lower()
        if text_in in quit_commands:
            raise ValueError("Quit")
        elif text_in in [p.lower() for p in ports]:
            return ports[[p.lower() for p in ports].index(text_in)]
        else:
            try:
                index = int(text_in)
                return ports[index]
            except (ValueError, IndexError):
                print('Given port not in the list. Try again. '
                      '(type q or quit to quit)')

if __name__ == '__main__':
    print(serial_ports())