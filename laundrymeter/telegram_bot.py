# -*- coding: utf-8 -*-
"""Telegram Bot responding to commands different commands.

Defines callbacks to Telegram commands, providing a subset of the REST Api.
Authentication is provided via a start token that has to be obtained via
the REST API first.

"""

from __future__ import annotations
from flask import g
from sqlalchemy import desc
from telegram.ext import Updater, CommandHandler
from functools import wraps
import atexit

from .models import User, WashingMachine, WashingMachineSchema


def telegram_auth_required(func):
    """Function wrapper to provide authentication on telegram commands."""
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        with app.app_context():
            user = User.query.filter_by(telegram_chat_id=update.message.chat_id).one()
            if not user:
                app.logger.info('Unauthorized Telegram message received from %d', update.message.chat_id)
                update.message.reply_text("Unauthorized. Please authenticate first.")
                return

            g.user = user
            app.logger.debug('User %s (%s) successfully authenticated command call', user.username, user.name)

            # Return inside app_context() to use same app context in called function. (to be able to use g)
            return func(bot, update, *args, **kwargs)
    return wrapped

def start(bot, update, args):
    """Telegram callback for the '/start' command send as first command in every chat."""
    with app.app_context():
        if not args:
            app.logger.debug("A user %s (%s) tried to start a chat with the telegram bot, without providing a token.",
                             update.message.from_user.full_name,
                             update.message.from_user.username)
            update.message.reply_text("Missing token. Please call `/start \{token\}` with the correct token to authenticate.")
            return

        update.message
        user = User.verify_telegram_token(token=args[0], chat_id=update.message.chat_id)

        if not user:
            app.logger.debug("A user %s (%s) provided an invalid token for authentication when calling /start",
                             update.message.from_user.full_name,
                             update.message.from_user.username)
            update.message.reply_text("Invalid token. Please call `/start \{token\}` with the correct token to authenticate.")
            return

        app.logger.debug('User %s (%s) successfully authenticated via telegram.', user.username, user.name)
        update.message.reply_text("Successfully authenticated!")

@telegram_auth_required
def notify(bot, update):
    """Telegram callback for `/notify` to regsiter a user to be notified when the laundry is ready."""
    try:
        g.user.register_notification(telegram=True)
        app.logger.debug('User %s (%s) successfully called notify(). He will be notified when the laundry is ready.', g.user.username, g.user.name)
        update.message.reply_text("You will be notified as soon as the laundry is ready.")
    except Exception as e:
        update.message.reply_text("There was an error registering you.")
        app.logger.exception("User %s (%s) raised an error on notify(). He couldn't be added for notification.", g.user.username, g.user.name)

@telegram_auth_required
def status(bot, update):
    """Telegram callback for `/status` to query the current simple status of the washing machine."""
    try:
        washing_machine = WashingMachine.query.order_by(desc('timestamp')).first()
        app.logger.debug('User %s (%s) successfully called status(). Current Wasching Machine status was returned: %s', g.user.username, g.user.name, washing_machine.running)
        update.message.reply_text("The Washing Machine is currently " + ("Running" if washing_machine.running else "Stopped"))
    except Exception as e:
        app.logger.exception("User %s (%s) raised an exception on status(). Couldn't retrieve it from the Database.", g.user.username, g.user.name)
        update.message.reply_text("Couldn't retrieve the current machine status.")

@telegram_auth_required
def debug(bot, update):
    """Telegram callback for `/debug` to query the current extended status of the washing machine."""
    try:
        washing_machine = WashingMachine.query.order_by(desc('timestamp')).first()
        wm_debug_schema = WashingMachineSchema()
        app.logger.debug('User %s (%s) successfully called debug(). Current Wasching Machine status was returned: %s', g.user.username, g.user.name, wm_debug_schema)
        update.message.reply_text(wm_debug_schema.dumps(washing_machine))
    except Exception as e:
        app.logger.exception("User %s (%s) raised an exception on debug(). Couldn't retrieve it from the Database.", g.user.username, g.user.name)
        update.message.reply_text("Couldn't retrieve the current machine status.")

def init_app(flask_app: Flask) -> None:
    """Initializing the telegram app with app context and registering callbacks"""
    flask_app.logger.debug('Initializing Telegram Bot...')
    global updater
    global app
    updater = Updater(flask_app.config['TELEGRAM_BOT_TOKEN'])
    app = flask_app

    updater.dispatcher.add_handler(CommandHandler('notify', notify))
    updater.dispatcher.add_handler(CommandHandler('start', start, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('status', status))
    updater.dispatcher.add_handler(CommandHandler('debug', debug))

    flask_app.logger.debug('Starting Telegram Message Poller...')
    updater.start_polling()
    atexit.register(lambda: updater.stop())
    flask_app.logger.debug('Finished setting up Telegram Bot.')
