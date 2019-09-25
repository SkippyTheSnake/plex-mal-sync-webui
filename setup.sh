#!/bin/sh
python3.7 createSetupfiles.py
rm /etc/nginx/sites-enabled/default
cp setupfiles/plex-mal-sync-webui.conf /etc/supervisor/conf.d/plex-mal-sync-webui.conf
cp setupfiles/plex-mal-sync-webui /etc/nginx/sites-enabled/plex-mal-sync-webui
python3.7 -m venv venv
venv/bin/pip3.7 install -r requirements.txt
touch err.log
touch out.log
sudo systemctl restart nginx
sudo supervisorctl update
sudo supervisorctl restart plex-mal-sync-webui