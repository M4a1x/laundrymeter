#!/bin/bash
pipenv run gunicorn -w 4 -b 0.0.0.0:8000 "laundrymeter:create_app()"