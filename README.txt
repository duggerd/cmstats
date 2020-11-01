sudo apt install rrdtool
sudo apt install python3-venv
python3 -m venv env
source env/bin/activate
pip install beautifulsoup4
pip install lxml
pip install requests
deactivate

/lib/systemd/system/cmstats.service

/lib/systemd/system/cmstats.timer

sudo systemctl daemon-reload

sudo systemctl enable cmstats.timer

sudo systemctl start cmstats.timer

sudo systemctl status cmstats.timer

sudo systemctl status cmstats

sudo ln -s /etc/nginx/sites-available/cmstats-site.conf /etc/nginx/sites-enabled/cmstats-site.conf
sudo ln -s /etc/nginx/modules-available/cmstats-module.conf /etc/nginx/modules-enabled/cmstats-module.conf
