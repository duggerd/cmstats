sudo apt install rrdtool
sudo apt install python3-venv
python3 -m venv env
source env/bin/activate
pip install beautifulsoup4
pip install lxml
deactivate

/lib/systemd/system/cmstats.service

/lib/systemd/system/cmstats.timer

sudo systemctl daemon-reload

sudo systemctl enable cmstats.timer

sudo systemctl start cmstats.timer

sudo systemctl status cmstats.timer

sudo systemctl status cmstats

/etc/nginx/sites-available/cmstats
