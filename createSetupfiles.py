import getpass
import socket
import os

PROJECT_NAME = 'plex-mal-sync-webui'
INTERNAL_PORT = 8002
PORT = 5002

username = getpass.getuser()
pwd = os.path.dirname(os.path.realpath(__file__))
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
server_ip = s.getsockname()[0]
s.close()

with open('setupfiles/plex-mal-sync-webui.conf', 'w') as f:
    f.write(f"""[program:{PROJECT_NAME}]
directory={pwd}
command={os.path.join(pwd, 'venv/bin/python')} main.py
user={username}
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile={os.path.join(pwd, 'err.log')}
stdout_logfile={os.path.join(pwd, 'out.log')}""")

with open('setupfiles/plex-mal-sync-webui', 'w') as f:
    f.write(f"""server {{
        listen {PORT};
        server_name {server_ip};

        location /static {{
            alias {os.path.join(pwd, 'static')};
        }}

        location / {{
            proxy_pass http://localhost:{INTERNAL_PORT};
            include /etc/nginx/proxy_params;
            proxy_redirect off;
        }}
    }}""")
