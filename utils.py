from datetime import datetime
from typing import Union

import schedule
from colorama import Style
import json
import os
import config
from config import RECENT_UPDATES_PATH
import sys


def log(text: str, *style: str) -> None:
    """ Logs text with a specified style using colorama styles """
    config.socketio.emit('new_log', {'log': text}, namespace = '/socket')
    config.latest_log = text
    timestamp = datetime.today().strftime('%d-%m-%Y %H:%M:%S')
    print(f"{timestamp} {''.join(style) + text}{Style.RESET_ALL}", file = sys.stdout)
    sys.stdout.flush()


def load_json(filepath: str, default_value: Union[list, dict] = None) -> Union[list, dict, None]:
    """ Opens json files and returns the parsed data.

    :param filepath: File path to the json file.
    :param default_value: The default value to create the file with if file doesn't exist.
    :return: Parsed json data file.
    """
    # Create file if it doesn't exist and return a blank dictionary
    if not os.path.exists(filepath):
        # If no default value was passed don't create the file
        if default_value is None:
            return None

        # If a default value was passed create the file
        save_json(default_value, filepath)
        return default_value

    # Load from existing file
    with open(filepath, 'r') as f:
        return json.load(f)


def save_json(data: Union[list, dict], filepath: str) -> None:
    """ Saved data to a json file at the specified file path

    :param data: The data to write to the json file.
    :param filepath: The path where the json file will be saved.
    """
    with open(filepath, 'w') as f:
        json.dump(data, f)


def get_countdown():
    next_run = schedule.jobs[0].next_run
    seconds = (next_run - datetime.now()).total_seconds()
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h < 0:
        h, m, s = 0, 0, 0

    return f'{int(h):02} : {int(m):02} : {int(s):02}'


def get_recent_updates():
    return load_json(RECENT_UPDATES_PATH, [])


def save_recent_updates(recent_updates: list):
    save_json(recent_updates[-10:], RECENT_UPDATES_PATH)
