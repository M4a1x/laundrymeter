# -*- coding: utf-8 -*-
"""Laundrymeter notifies you when the laundry is ready

It consists of an REST API part as main interaction point with different
notifiers available. The status of the machine is queried every n seconds
and written to a database. When a state change running -> stopped is 
detected it sends out a notification to subscribed users.

"""

import os
from flask import Flask
import logging

from .apis import bp as api
from .models import db, ma
from . import telegram_bot
from . import wm_poller
from . import db_helper
from . import dashboard


# Application Factory
def create_app(test_config=None):
    """The application factory."""
    
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.logger.setLevel(logging.DEBUG)
    app.logger.debug("Setting up main application...")

    # Default config
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI='sqlite:///'+os.path.join(app.instance_path,
                                                          'db.sqlite'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
    
        # Custom config
        LDAP_URL="ldap.example.org",
        LDAP_BASE_DN="DC=example, DC=org",
        SMART_PLUG_IP='192.168.1.100',
        SMTP_EMAIL='test@example.org',
        SMTP_PASSWORD='dev',
        TELEGRAM_BOT_TOKEN='dev',
        POLL_INTERVAL=5,                # The washing machine will be polled every 5 seconds
        RUNNING_THRESHOLD_POWER = 80,   # below 80 Watts, the machine will be considered "not running"
        RUNNING_THRESHOLD_TICKS = 56    # after 56 Ticks (a 5 sec) it will be considered "off"
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Register flask-restplus
    app.register_blueprint(api, url_prefix='/api')

    # Initialize SQLAlchemy Database
    db.init_app(app)

    # Register init-db command/init app
    db_helper.init_app(app)

    # Register Marshmallow (after SQLAlchemy)
    ma.init_app(app)

    # Init telegram bot
    telegram_bot.init_app(app)

    # Init Washing Machine poller
    wm_poller.init_app(app)

    # Create Dash app (after SQLAlchemy!)
    dashboard.init_app(app)

    app.logger.debug("Finished setting up main application.")
    return app