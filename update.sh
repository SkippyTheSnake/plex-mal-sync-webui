#!/bin/sh
git pull
venv/bin/pip3.7 install -r requirements.txt
sudo supervisorctl restart plex-mal-sync-webui
