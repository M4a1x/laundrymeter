Washing Machine App
===================

Installation
------------

* python3 & pip3
* `pip install -r requirements.txt`

Configuration
-------------

* VM IP: 100.117.66.20
* Needs the following connections:
    * TP-Link Smartplug, in local network 192.168.22.3
    * LDAP-Server, SSL-Port [ldap.example.org:636](192.168.21.10:636)
    * Internet, Port 443 for Secure HTTPS Traffic

Washing Machine Stats
---------------------
* Closed door, not running, but on: 2.2W, current: 33mA
* Open door, not running, but on: 0W, current: 42mA
* Off: 0W, 42mA

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
* Write dockerfiles to encapsulate the service
* Write docker-compose script (or so) to integrate different containers (nginx, python, ...)