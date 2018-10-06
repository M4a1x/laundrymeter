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


Configuration
-------------

* VM IP: 100.117.66.20
* Needs the following connections:
    * TP-Link Smartplug, in local network 192.168.22.3
    * LDAP-Server, SSL-Port [ldap.example.org:636](192.168.21.10:636)
    * Internet, Port 443 for HTTPS (with e.g. nginx) or 80 local if forwarded to public internet


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


Roadmap
-------

* Use techniques from [Flask Tutorial](http://flask.pocoo.org/docs/1.0/tutorial/layout/) and [flask-restplus Scaling](https://flask-restplus.readthedocs.io/en/0.11.0/scaling.html)
* Modularize app.py, maybe use schedule then, instead of apscheduler (celery is probably overkill)
* Write better documentation (function, class, etc.)
* Write better api documentation (swagger)
* Write tests!
* Implement Logging!
* Better exception Handling (no plug detected, wrong parameters, ...)
* export config to seperate file
* Write setup.py for installation (to docker conainter?)
* Write systemd service file
* Write dockerfiles to encapsulate the service
* Write docker-compose script (or so) to integrate different containers (nginx, python, ...)
* Write analysis tool/graph (plotly?)