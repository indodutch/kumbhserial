# -*- coding: utf-8 -*-
"""
Created on Fri Apr 08 12:13:28 2016

@author: Zoli
"""
from __future__ import print_function

import os
from .kumbhm_dumper import dumper_main
from .kumbhm_processor import KumbhMelaProcessor
from .serial_tools import resolve_serial_port
from .version import __version__
import sys
import docopt
import serial


def main(argv=sys.argv[1:]):
    """
    Listens to a device and dumps it
    Usage:
      kumbhserial [-h] [-V] [--output dir] [--tmp dir] [<device_num>]

    Options:
      <device_num>       TTY or serial port number or name to listen to
      -h, --help         This help text
      -t, --tmp dir      Temporary directory [default: data]
      -o, --output dir   Output directory [default: data/processed/raw/]
      -V, --version      Version information
    """
    arguments = docopt.docopt(main.__doc__, argv, version=__version__)

    try:
        chosen_port = resolve_serial_port(arguments['<device_num>'])
    except ValueError as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

    try:
        dumpfile = dumper_main(chosen_port, tmp_dir=arguments['--tmp'])
    except serial.SerialException as e:
        print("Cannot start serial connection: {0}".format(e))
        sys.exit(1)

    if dumpfile:
        fid = os.path.splitext(os.path.basename(dumpfile))[0]
        proc = KumbhMelaProcessor(fid)
        with open(dumpfile, 'rb') as fh:
            n_data = proc.process_file(fh)
        print('%d frames processed' % (n_data,))
        move_path = arguments['--output']
        if not os.path.exists(move_path):
            os.mkdir(move_path)
        new_dumppath = os.path.join(move_path, os.path.basename(dumpfile))
        os.rename(dumpfile, new_dumppath)
        print('backup saved to ' + new_dumppath)

if __name__ == "__main__":
    main()
