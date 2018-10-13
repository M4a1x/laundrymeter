#!/bin/bash
pipenv run gunicorn -w 1 -b 0.0.0.0:8000 --capture-output --error-logfile "laundrymeter-err.log" --log-file "laundrymeter.log" --log-level debug "laundrymeter:create_app()"