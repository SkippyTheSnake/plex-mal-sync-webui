from datetime import datetime
import time

import schedule
from flask import Flask, render_template, jsonify, request
import threading
import mapping
import utils
from config import MAPPING_ERRORS_FILEPATH, SYNC_TIME
import config
from syncHandler import do_sync
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)
config.socketio = socketio


def sync_runner():
    if not config.sync_running:
        config.sync_running = True
        socketio.emit('update_sync_running', {'sync_running': True}, namespace = '/socket')
        do_sync()
        config.sync_running = False
        socketio.emit('update_sync_running', {'sync_running': False}, namespace = '/socket')


def start_schedule():
    schedule.every().day.at(SYNC_TIME).do(sync_runner)
    while True:
        schedule.run_pending()
        time.sleep(1)  # wait one minute


thread = threading.Thread(target = start_schedule)
thread.start()


@app.route('/')
def index():
    num_errors = len(utils.load_json(MAPPING_ERRORS_FILEPATH, {}))
    num_errors = '' if num_errors == 0 else num_errors

    recent_updates = "\n".join(utils.get_recent_updates())

    next_run = schedule.jobs[0].next_run
    time_remaining = (next_run - datetime.now()).total_seconds()

    return render_template('index.html', countdown = utils.get_countdown(), num_errors = num_errors,
                           recent_updates = recent_updates, sync_running = str(config.sync_running).lower(),
                           time_remaining = time_remaining, latest_log = config.latest_log)


@app.route('/api/driver_screenshot')
def driver_screenshot():
    if config.DRIVER is not None:
        config.DRIVER.save_screenshot()
        
    return jsonify({})


@app.route('/mapping_errors', methods = ['GET', 'POST'])
def mapping_errors():
    if request.method == 'POST':
        form_data = request.form
        for k, mal_id in form_data.items():
            mal_id = mal_id.strip()
            if mal_id == '':
                continue
            tvdbid, season = [x.strip() for x in k.lstrip('formData').split('|')]
            mapping.add_tvdbid_malid_mapping(tvdbid, season, mal_id)

    errors = utils.load_json(MAPPING_ERRORS_FILEPATH, {})
    return render_template('mappingErrors.html', errors = errors)


@app.route('/api/run_sync')
def run_sync():
    sync_runner()
    return jsonify({})


if __name__ == '__main__':
    socketio.run(app, port = 8002)
