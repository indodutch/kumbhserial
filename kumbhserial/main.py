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
Main functions to run scripts from.
"""

from __future__ import print_function

from .gps import GpsReaderThread
from .helpers import output_filename, dir_files
from .interpreter import (SeparatedTrackerEntrySetJsonConverter,
                          TrackerInterpreter)
from .reader import run_reader, read_file, ReaderSet
from .sniffer import SnifferInterpreter
from .appenders import (Dumper, JsonListAppender, Duplicator, ThreadBuffer,
                        RawPrinter)
from .ports import resolve_serial_port, choose_serial_port
from .version import __version__
import sys
import os
import shutil
import docopt
import serial


def download(argv=sys.argv[1:]):
    """
    Listens to a device and dumps it in raw text and JSON format.
    if --no-json is specified, only to [DATA]/raw. Output goes to
    [DATA]/raw/processed and to [DATA]/system and [DATA]/detection.
    Usage:
      kumbhdownload [-h] [-V] [--data dir] [--no-json] [<device_num>]

    Options:
      <device_num>       TTY or serial port number or name to listen to
      -d, --data dir     Data base directory [default: ./data]
      -J, --no-json      Do not output to JSON, only to raw text.
      -h, --help         This help text
      -V, --version      Version information
    """
    arguments = docopt.docopt(download.__doc__, argv, version=__version__)

    chosen_port = resolve_port(arguments['<device_num>'])

    port_id = chosen_port.split('/')[-1]
    if arguments['--no-json']:
        appender = Dumper(output_filename(os.path.join(arguments['--data'],
                                                       'raw'),
                                          'dump-' + port_id, 'txt'))
    else:
        dumper = Dumper(output_filename(os.path.join(arguments['--data'],
                                                     'raw', 'processed'),
                                        'dump-' + port_id, 'txt'))
        filename_detections = output_filename(
            os.path.join(arguments['--data'], 'detection'),
            'detection-' + port_id, 'json')
        filename_system = output_filename(
            os.path.join(arguments['--data'], 'system'),
            'system-' + port_id, 'json')
        tracker = TrackerInterpreter(
            SeparatedTrackerEntrySetJsonConverter(
                JsonListAppender(Dumper(filename_detections, flush=False)),
                JsonListAppender(Dumper(filename_system, flush=False))))
        appender = Duplicator([ThreadBuffer(tracker), dumper])

    read_device(chosen_port, appender)


def sniffer(argv=sys.argv[1:]):
    """
    Listens to the sniffer node and outputs the real time and network time
    in JSON format. Output goes to $DATA/sniffer.
    Usage:
      kumbhsniffer [-h] [-V] [--data dir] [--print] [<device_num>]

    Options:
      <device_num>       TTY or serial port number or name to listen to
      -d, --data dir     Data base directory [default: data]
      -p, --print        Print data to screen
      -h, --help         This help text
      -V, --version      Version information
    """
    arguments = docopt.docopt(sniffer.__doc__, argv, version=__version__)

    chosen_port = resolve_port(arguments['<device_num>'])
    filename = output_filename(os.path.join(arguments['--data'], 'sniffer'),
                               'sniffer', 'json')
    appender = JsonListAppender(Dumper(filename))
    if arguments['--print']:
        appender = Duplicator([appender, RawPrinter()])

    interpreter = SnifferInterpreter(appender)
    read_device(chosen_port, interpreter, heartbeat=None)


def processor(argv=sys.argv[1:]):
    """
    Process raw files and convert them to JSON. Input is all files in
    [DATA]/raw and output goes to [DATA]/system and [DATA]/detection. The
    original file is moved to [DATA]/raw/processed.

    Usage:
      kumbhprocessor [-h] [-V] [--data dir] [<input>]

    Options:
      <input>            File or directory to read from, if not [DATA]/raw.
      -d, --data dir     Data base directory [default: data]
      -h, --help         This help text
      -V, --version      Version information
    """
    arguments = docopt.docopt(processor.__doc__, argv, version=__version__)

    if arguments['<input>']:
        if os.path.isdir(arguments['<input>']):
            files = dir_files(arguments['<input>'])
        elif os.path.exists(arguments['<input>']):
            files = [arguments['<input>']]
        else:
            sys.exit('Input path {0} does not exist.'
                     .format(arguments['<input>']))
    else:
        input_path = os.path.join(arguments['--data'], 'raw')
        try:
            files = dir_files(input_path)
        except FileNotFoundError:
            sys.exit('Input path {0} does not exist.'
                     .format(input_path))

    processed_dir = os.path.join(arguments['--data'], 'raw', 'processed')

    if len(files) == 0:
        print("No files to be processed")
        return

    if not os.path.exists(processed_dir):
        os.mkdir(processed_dir)

    for i, path in enumerate(files):
        filename = os.path.basename(path)
        print("Converting {0} out of {1}: {2}"
              .format(i + 1, len(files), filename))
        base = os.path.splitext(filename)[0]
        filename_detections = output_filename(
            os.path.join(arguments['--data'], 'detection'),
            'detection-' + base, 'json')
        filename_system = output_filename(
            os.path.join(arguments['--data'], 'system'),
            'system-' + base, 'json')
        tracker = TrackerInterpreter(
            SeparatedTrackerEntrySetJsonConverter(
                JsonListAppender(Dumper(filename_detections, flush=False)),
                JsonListAppender(Dumper(filename_system, flush=False))))

        read_file(path, tracker)

        try:
            shutil.move(path, processed_dir)
        except OSError as ex:
            print("Failed to move {0} to {1}: {2}"
                  .format(path, processed_dir, ex))


def gps(argv=sys.argv[1:]):
    """
    Process raw files and convert them to JSON. Input is all files in
    [DATA]/raw and output goes to [DATA]/system and [DATA]/detection. The
    original file is moved to [DATA]/raw/processed.

    Usage:
      kumbhgps [-h] [-V] [--data dir] [--format format] [--no-lookup] [--no-clear] [--listen] [<device_num>]

    Options:
      <device_num>         TTY or serial port number or name to listen to
      -l, --listen         Keep listening for devices.
      -C, --no-clear       Do not clear the device after reading
      -d, --data dir       Data base directory [default: data]
      -h, --help           This help text
      -L, --no-lookup      Do not look up the device number
      -V, --version        Version information
    """
    arguments = docopt.docopt(gps.__doc__, argv, version=__version__)

    if arguments['--listen']:
        continuous_gps(arguments)
        return

    if not arguments['--no-lookup']:
        chosen_port = resolve_port(arguments['<device_num>'])
    elif arguments['<device_num>']:
        chosen_port = arguments['<device_num>']
    else:
        sys.exit('Provide a device if specifying --no-lookup')

    filename = output_filename(os.path.join(arguments['--data'], 'gps'),
                               'gps', 'json')

    try:
        reader = GpsReaderThread(chosen_port,
                                 JsonListAppender(Dumper(filename)),
                                 clear=not arguments['--no-clear'])
    except serial.SerialException as ex:
        print('Cannot open serial port {0}: {1}'.format(chosen_port, ex))
    else:
        reader.start()
        reader.join()
        print("Quit.")


def continuous_gps(arguments):
    """
    Continuously listen for new GPS devices.
    :param arguments: dict of arguments from docopt
    """
    readers = ReaderSet()
    try:
        while True:
            chosen_port = choose_serial_port(readers)
            filename = output_filename(
                os.path.join(arguments['--data'], 'gps'), 'gps', 'json')
            try:
                readers.start(GpsReaderThread(
                    chosen_port, JsonListAppender(Dumper(filename)),
                    clear=not arguments['--no-clear']))
            except serial.SerialException as ex:
                print('Cannot open serial port {0}: {1}'
                      .format(chosen_port, ex))
    except ValueError as ex:
        readers.stop()
        print(ex)
        sys.exit(0)
    except KeyboardInterrupt as ex:
        readers.stop()
        sys.exit(ex)


def resolve_port(port):
    """
    Resolve given port or query the user for it. The function will exit if the
    user indicates it.
    :param port: serial port name, number or None
    :return: valid serial port name
    """
    try:
        chosen_port = resolve_serial_port(port)
    except ValueError as ex:
        sys.exit(ex)

    try:
        if chosen_port is None:
            chosen_port = choose_serial_port()
    except ValueError as ex:
        print(ex)
        sys.exit()
    except KeyboardInterrupt as ex:
        sys.exit(ex)

    return chosen_port


def read_device(port, appender, **kwargs):
    """
    Reads a given device and send the output to given appender. Runs run_reader
    internally, and it will exit if the user quits.
    :param port: serial port name
    :param appender: appender to write the data to
    :param kwargs: other arguments to run_reader
    """
    try:
        run_reader(port, appender, **kwargs)
    except serial.SerialException as e:
        sys.exit("Cannot start serial connection: {0}".format(e))
    except ValueError:
        print("Quit")
        sys.exit()
    except KeyboardInterrupt:
        sys.exit("Force quit")
