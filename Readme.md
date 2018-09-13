Washing Machine App
===================

Installation
------------

* python3 & pip3
* `pip install -r requirements.txt`

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