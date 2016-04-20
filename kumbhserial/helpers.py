import sys
from datetime import datetime, timezone


def text_in(quit_commands=('q', 'quit')):
    try:
        text = sys.stdin.readline().strip().lower()
        if text in quit_commands:
            raise ValueError('Quit')
        return text
    except KeyboardInterrupt:
        raise ValueError('Quit')


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
    return datetime.now(timezone.utc).astimezone().isoformat()


def insert_timestamp(text, token, separator=b'%'):
    index = text.find(token)
    if index != -1:
        return (text[:index + len(token)] + separator +
                bytes(timestamp(), encoding='ascii') +
                separator + text[index + len(token):])
    else:
        return text
