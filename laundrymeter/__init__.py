import os
from flask import Flask

from apis import bp as api
from models import db
import db_helper


# Application Factory
def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # Default config
    app.config.from_mapping(
        #SECRET_KEY='dev', # used by flask for signing session cookie, do I use it? -> No.
        JWT_SECRET_KEY='dev',
        JWT_ACCESS_TOKEN_EXPIRES=False,
        SQLALCHEMY_DATABASE_URI='sqlite:///'+os.path.join(app.instance_path,
                                                          'db.sqlite'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    
        # Custom config
        LDAP_URL="ldap.example.org",
        LDAP_BASE_DN="DC=example, DC=org",
        SMART_PLUG_IP='192.168.1.100',
        SMTP_EMAIL='test@example.org',
        SMTP_PASSWORD='dev',
        TELEGRAM_BOT_TOKEN='dev'
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Register flask-restplus
    app.register_blueprint(api)

    # Initialize SQLAlchemy Database
    db.init_app(app)

    # Register init-db command/init app
    db_helper.init_app(app)

    return app