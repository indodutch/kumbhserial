# -*- coding: utf-8 -*-
"""
Created on Fri Apr 08 12:13:28 2016

@author: Zoli
"""
from __future__ import print_function

from kumbhserial.helpers import output_filename
from kumbhserial.interpreter import SeparatedTrackerEntrySetJsonConverter, \
    TrackerInterpreter
from kumbhserial.reader import run_reader
from kumbhserial.sniffer import SnifferInterpreter
from .appenders import Dumper, JsonListAppender, create_dumper_file, Duplicator, \
    ThreadBuffer
from .ports import resolve_serial_port, choose_serial_port
from .version import __version__
import sys
import os
import docopt
import serial


def resolve_port(port):
    try:
        chosen_port = resolve_serial_port(port)
    except ValueError as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

    try:
        if chosen_port is None:
            chosen_port = choose_serial_port()
    except ValueError as ex:
        print(ex)
        print("Quit.")
    except KeyboardInterrupt as ex:
        print(ex)
        print("Force quit.")

    return chosen_port


def read_device(port, appender, **kwargs):
    try:
        run_reader(port, appender, **kwargs)
    except serial.SerialException as e:
        print("Cannot start serial connection: {0}".format(e))
        sys.exit(1)
    except (ValueError, KeyboardInterrupt):
        print("Quit.")


def download(argv=sys.argv[1:]):
    """
    Listens to a device and dumps it
    Usage:
      kumbhdownload [-h] [-V] [--output dir] [--json] [<device_num>]

    Options:
      <device_num>       TTY or serial port number or name to listen to
      -h, --help         This help text
      -o, --output dir   Output base directory [default: ./data]
      -j, --json         Also output to JSON
      -V, --version      Version information
    """
    arguments = docopt.docopt(download.__doc__, argv, version=__version__)

    chosen_port = resolve_port(arguments['<device_num>'])
    port_id = chosen_port.split('/')[-1]
    filename = output_filename(os.path.join(arguments['--output'], 'raw'),
                               'dump-' + port_id, 'txt')
    appender = Dumper(filename)
    if arguments['--json']:
        filename_detections = output_filename(
            os.path.join(arguments['--output'], 'detection'),
            'detection-' + port_id, 'json')
        filename_system = output_filename(
            os.path.join(arguments['--output'], 'system'),
            'system-' + port_id, 'json')
        tracker = TrackerInterpreter(
            SeparatedTrackerEntrySetJsonConverter(
                JsonListAppender(Dumper(filename_detections)),
                JsonListAppender(Dumper(filename_system))))
        appender = Duplicator([ThreadBuffer(tracker), appender])

    read_device(chosen_port, appender)

def sniffer(argv=sys.argv[1:]):
    """
    Listens to a device and dumps it
    Usage:
      kumbhsniffer [-h] [-V] [--output dir] [<device_num>]

    Options:
      <device_num>       TTY or serial port number or name to listen to
      -h, --help         This help text
      -o, --output dir   Output directory [default: ./data]
      -V, --version      Version information
    """
    arguments = docopt.docopt(sniffer.__doc__, argv, version=__version__)

    chosen_port = resolve_port(arguments['<device_num>'])
    filename = output_filename(os.path.join(arguments['--output'], 'sniffer'),
                               'sniffer', 'json')
    interpreter = SnifferInterpreter(JsonListAppender(Dumper(filename)))
    read_device(chosen_port, interpreter, heartbeat=False)
