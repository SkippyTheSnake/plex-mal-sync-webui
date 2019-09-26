import os
import sys
import json

env_data_path = os.environ.get('PROGRAM_DATA_PATH')
if env_data_path is None:
    print("Error please set an environment variable for PROGRAM_DATA_PATH")
    sys.exit()

# Fixed
DATA_PATH = os.path.join(env_data_path, 'plex-mal-sync-webui')
if not os.path.exists(DATA_PATH):
    os.mkdir(DATA_PATH)

TVDBID_ANIDBID_XML_FILEPATH = os.path.join(DATA_PATH, 'tvdbid_to_anidbid.xml')
TVDBID_ANIDBID_FILEPATH = os.path.join(DATA_PATH, 'tvdbid_to_anidbid.json')
TVDBID_MALID_FILEPATH = os.path.join(DATA_PATH, 'tvdbid_to_malid.json')
MAPPING_ERRORS_FILEPATH = os.path.join(DATA_PATH, 'mapping_errors.json')
RECENT_UPDATES_PATH = os.path.join(DATA_PATH, 'recent_updates.json')
CONFIG_PATH = os.path.join(DATA_PATH, 'config_data.json')
DRIVER = None

if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'w') as f:
        json.dump({'LIBRARY'     : None,
                   'SERVER_TOKEN': None,
                   'SERVER_URL'  : None,
                   'MAL_USERNAME': None,
                   'MAL_PASSWORD': None,
                   'SYNC_TIME'   : '19:00'}, f)
    print("Please fill in the values in the config file")
    sys.exit()

with open(CONFIG_PATH, 'r') as f:
    data = json.load(f)

# Check that all config values have been filled in
unfilled_values = [k for k, v in data.items() if v in [None, 'none', 'null']]
if len(unfilled_values) > 0:
    print("Please fill in the following config values: " + ", ".join(unfilled_values))
    sys.exit()

# Configurable
LIBRARY = data.get('LIBRARY')
SERVER_TOKEN = data.get('SERVER_TOKEN')
SERVER_URL = data.get('SERVER_URL')
MAL_USERNAME = data.get('MAL_USERNAME')
MAL_PASSWORD = data.get('MAL_PASSWORD')
SYNC_TIME = '19:00'

# Changing
latest_log = ""
sync_running = False
socketio = None
