Washing Machine App
===================

Installation
------------

* Requires git, python3
    * `curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py`
    * `python get-pip.py --user`
    * `pip install --user pipenv`
* Clone repository: `git clone https://github.com/M4a1x/laundrymeter`
* Enter directory: `cd laundrymeter`
* Install dependencies: `pipenv install`
* Run `./start_development.sh` or `./start_production.sh`

To run the server on port 80 (or other port < 1024)

* Change the script accordingly (i.e. substitute `8000` with `80`)
* Install `authbind` (as root)
* i.e. add all users to be able to use port 80: `touch /etc/authbind/byport/80` and `chmod 777 /etc/authbind/byport/80` (also as root)
* Start the script: `authbind --deep start_production.sh`

To be able to logout from ssh after starting the server

* Use `nohup authbind --deep sh start_production.sh &`
* or `tmux` / `screen`

Configuration
-------------

* VM IP: 100.117.66.20
* Needs the following connections:
    * TP-Link Smartplug (for sensor readout), in 192.168.22.3
    * LDAP-Server, SSL-Port [192.168.21.10:636](192.168.21.10:636), for authentication
    * Port 587 to connect to gmail via STARTTLS, to send notifications
    * Port 8000 for unencrypted access to REST Api. Reverse proxy for https is recommended.

Washing Machine Stats
---------------------

* Closed door, not running, but on: 2.2W, current: 33mA
* Open door, not running, but on: 0W, current: 42mA
* Off: 0W, 42mA
* Finished: < 50W distinct pattern, sharp spikes with pauses
* Heating: > 2000W Temperature can probably be infered from duration

Running Detection
-----------------

Problem

* Machine pauses after heatup. 3min, 2min
    * -> Threshold of 50W, delay of 4min (48 ticks)

Other ideas:

* Simple Threshold
* Signal Energy, AKF
* Double Threshold
* Timed Threshold
