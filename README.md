# Plex-mal-sync-webui
A program to sync MyAnimeList with a plex library so that you no longer need to update MyAnimeList manually.

## Installation
This program is designed to be run on a Ubuntu server.\
You must have an environment variable `PROGRAM_DATA_PATH` and set it to the path where all the program data is going to be located.\
If you are using supervisor this can be set in the ''/etc/supervisor/supervisord.conf''.\
Run the program and it will generate a config file in the data location.\
Fill in that data and the then the program is ready.\
You will also need chromedriver on the server to run the updater.\
\
Create a virtual environment for the project and install the requirements into it.
```
$ python -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
 ```
You should use supervisord to run the program and nginx to forward the requests.\
The setupfiles can be used to configure these.
## Sources
Tvdb to anidb mappings obtained from [ScudLee - anime-list](https://github.com/ScudLee/anime-lists)