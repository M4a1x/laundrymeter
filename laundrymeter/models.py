# -*- coding: utf-8 -*-
"""SQLAlchemy models for Database interaction

This module contains a User class for storing user information. No password
is stored as authentication is handled through ldap. It does store a token,
if desired by the user. The user class contains information needed for
notification via email and telegram as well as booleans indicating whether
the user wants to be notified via the corresponding method.

"""

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import inspect
import secrets


# Main SQLAlchemy instance
db = SQLAlchemy()

# Main Marshmallow instance
ma = Marshmallow()


##################
##### Models #####
##################

class User(db.Model):
    """Representing a user with config. Authentication is handled in ldap."""

    __tablename__ = 'user'
    username = db.Column(db.String(255), primary_key=True)
    email = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255), unique=True)
    auth_token = db.Column(db.String(255), unique=True)
    notify_email = db.Column(db.Boolean)
    notify_telegram = db.Column(db.Boolean)
    telegram_chat_id = db.Column(db.Integer, unique=True)
    telegram_token = db.Column(db.String(255), unique=True)

    def generate_auth_token(self) -> str:
        """Generate a new auth token and store it in the database.
        
        Overwrites any existing token.

        Returns:
            The authentication token added to the database
        """

        session = inspect(self).session
        self.auth_token = secrets.token_urlsafe()
        session.commit()
        return self.auth_token

    @staticmethod
    def verify_auth_token(token: str) -> User:
        """Verify auth token and return corresponding user object.
        
        Returns:
            The object of the authenticated user, None otherwise.
        """
        try:
            user = User.query.filter_by(auth_token=token).one()
        except:
            user = None
        return user

    def generate_telegram_token(self) -> str:
        """Generate a new telegram token and store it in the database.
        
        Overwrites any existing token, thus logging out currently authenticated chats.

        Returns:
            The telegram token added to the database.
        """

        session = inspect(self).session
        self.telegram_token = secrets.token_urlsafe()
        session.commit()
        return self.telegram_token

    @staticmethod
    def verify_telegram_token(token: str, chat_id: int) -> User:
        """Verify telegram token delete it from database and return corresponding user object.
        
        Args:
            token: Telegram token to be verified (usually received through 
                   `/start {token}` command
            chat_id: The id of the chat that the token was recieved on, i.e.
                     the chat to be verified.

        Returns:
            The verified user object on success, None otherwise.

        """

        try:
            user = User.query.filter_by(telegram_token=token).one()
            session = inspect(user).session
            user.telegram_token = None
            user.telegram_chat_id = chat_id
            session.commit()
        except:
            current_app.logger.exception('Failed to verify telegram token %s send by %d', token, chat_id)
            user = None
        return user

    def register_notification(self, **kwargs) -> None:
        """Register supplied notifications.
        
        Args:
            email (Bool): True to enable notification by email for next event.
            telegram (Bool): True to enable notification via telegram for next event.
            
        """
        # TODO: Test what happens when argument is same as value. (Does session.commit throw an exception?)
        if kwargs:
            session = inspect(self).session
            if 'email' in kwargs:
                self.notify_email = kwargs['email']
            if 'telegram' in kwargs:
                self.notify_telegram = kwargs['telegram']
            session.commit()
        else:
            current_app.logger.debug('register_notification() called without arguments')


class WashingMachine(db.Model):
    """Model for storing current status of the Washing Machine in the DB."""
    __tablename__ = 'washingmachine'
    timestamp = db.Column(db.DateTime, primary_key=True)
    running = db.Column(db.Boolean)
    last_changed = db.Column(db.DateTime)
    voltage = db.Column(db.Float)
    current = db.Column(db.Float)
    power = db.Column(db.Float)
    total_power = db.Column(db.Float)


###################
##### Schemas #####
###################

class WashingMachineSchema(ma.ModelSchema):
    """Schema for JSON (De-)Serialization of Washing Machine."""
    class Meta:
        model = WashingMachine


class UserSchema(ma.ModelSchema):
    """Schema for JSON (De-)Serialization of User."""
    class Meta:
        model = User
