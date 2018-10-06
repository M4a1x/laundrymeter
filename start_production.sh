#!/bin/bash
pipenv run gunicorn -w 4 -b 0.0.0.0:80 "laundrymeter:create_app()"