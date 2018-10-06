#!/bin/bash
export FLASK_ENV=development
export FLASK_APP=laundrymeter
pipenv run flask run --no-reload -p 8000
