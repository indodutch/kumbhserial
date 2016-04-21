# -*- coding: utf-8 -*-
"""
Created on Fri Apr 08 12:13:28 2016

@author: Zoli
"""
from __future__ import print_function

from kumbhserial.helpers import output_filename
from kumbhserial.reader import run_reader
from kumbhserial.sniffer import SnifferInterpreter
from .appenders import Dumper, JsonListAppender, create_dumper_file
from .ports import resolve_serial_port, choose_serial_port
from .version import __version__
import sys
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
      kumbhserial [-h] [-V] [--output dir] [--tmp dir] [<device_num>]

    Options:
      <device_num>       TTY or serial port number or name to listen to
      -h, --help         This help text
      -t, --tmp dir      Temporary directory [default: data]
      -o, --output dir   Output directory [default: data/raw/]
      -V, --version      Version information
    """
    arguments = docopt.docopt(download.__doc__, argv, version=__version__)

    chosen_port = resolve_port(arguments['<device_num>'])
    filename = create_dumper_file(chosen_port, tmp_dir=arguments['--tmp'])
    read_device(chosen_port, Dumper(filename))


def sniffer(argv=sys.argv[1:]):
    """
    Listens to a device and dumps it
    Usage:
      kumbhsniffer [-h] [-V] [--output dir] [<device_num>]

    Options:
      <device_num>       TTY or serial port number or name to listen to
      -h, --help         This help text
      -o, --output dir   Output directory [default: data/sniffer]
      -V, --version      Version information
    """
    arguments = docopt.docopt(sniffer.__doc__, argv, version=__version__)

    chosen_port = resolve_port(arguments['<device_num>'])
    filename = output_filename(arguments['--output'], 'sniffer', 'json')
    interpreter = SnifferInterpreter(JsonListAppender(Dumper(filename)))
    read_device(chosen_port, interpreter, heartbeat=False)
