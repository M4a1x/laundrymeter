#!/bin/bash
export FLASK_ENV="development"
export FLASK_APP="laundrymeter:create_app()"
pipenv run flask run --no-reload -p 8000
