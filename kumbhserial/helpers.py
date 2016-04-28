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
Helper functions for IO and time.
"""

import sys
from datetime import datetime, timezone
import os
import time


def output_filename(directory, prefix, extension):
    """
    Create an output file in given directory with given prefix, a timestamp,
    and given extension. The directory will be created if it does not exist.
    :param directory: directory path to put the file in
    :param prefix: file prefix
    :param extension: file extension
    :return: file path
    :raise IOError: directory could not be created.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    return os.path.join(directory, '{0}-{1}.{2}'.format(
        prefix, time.strftime("%Y%m%d-%H%M%S"), extension))


def text_in(quit_commands=('q', 'quit')):
    """
    Allow a user to enter text in a terminal prompt.
    :param quit_commands: valid commands to indicate the user wants to quit
    :raise ValueError: user quit by typing quit command.
    :raise KeyboardInterrupt: user quit by sending an interrupt.
    :return: text entered
    """
    text = sys.stdin.readline().strip().lower()
    if text in quit_commands:
        raise ValueError('Quit')
    return text


def select_value_from_list(text, value_list):
    """
    :param text: value (case insensitive) or index of value list or None
    :param value_list: list of strings to choose from
    :return: chosen value, or if text is None, None
    :raises ValueError: if the string is not a valid value and not an index
    :raises IndexError: if given index is invalid
    """
    if text is None:
        return None
    if text in [p.lower() for p in value_list]:
        return value_list[[p.lower() for p in value_list].index(text)]
    else:
        return value_list[int(text)]


def timestamp():
    """
    ISO timestamp with timezone.
    :return: string of the current time.
    """
    return datetime.now(timezone.utc).astimezone().isoformat()


def insert_timestamp(text, token, separator=b'%'):
    """
    Insert a ISO timestamp in given text after any place that given token is
    encountered. The timestamp is wrapped in two separator tokens.
    :param text: bytes of text
    :param token: bytes token to insert timestamp after
    :param separator: text to wrap the timestamp in
    :return: bytes of text
    """
    index = text.find(token)
    if index != -1:
        return (text[:index + len(token)] + separator +
                bytes(timestamp(), encoding='ascii') +
                separator + text[index + len(token):])
    else:
        return text


def dir_files(dir_name):
    """
    Find all files in given directory, non-recursively.
    :param dir_name: directory path
    :return: list of file names
    """
    return [os.path.join(dir_name, f)
            for f in os.listdir(dir_name)
            if os.path.isfile(os.path.join(dir_name, f))]
