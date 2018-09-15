from sqlalchemy import desc
from telegram.ext import Updater, CommandHandler
from functools import wraps
import atexit

from .models import User, WashingMachine


# TODO: Docstring

def telegram_auth_required(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        user = User.query.filter_by(telegram_chat_id=update.message.chat_id).one()
        if not user:
            update.message.reply_text("Unauthorized. Please authenticate first.")
            return

        g.user = user
        return func(bot, update, *args, **kwargs)
    return wrapped

def start(bot, update, args):
    if not args:
        update.message.reply_text("Missing token.")
        return

    user = User.verify_telegram_token(token=args[0], chat_id=update.message.chat_id)

    if not user:
        update.message.reply_text("Invalid token.")
        return

    update.message.reply_text("Successfully authenticated!")

@telegram_auth_required
def notify(bot, update):
    g.user.register_notification(telegram=True)
    update.message.reply_text("You will be notified as soon as the laundry is ready.")

@telegram_auth_required
def status(bot, update):
    washing_machine = WashingMachine.query.order_by(desc('timestamp')).first()
    update.message.reply_text("Running" if washing_machine.running else "Stopped") 

def init_app(app):
    global updater
    updater = Updater(app.config['TELEGRAM_BOT_TOKEN'])

    updater.dispatcher.add_handler(CommandHandler('notify', notify))
    updater.dispatcher.add_handler(CommandHandler('start', start, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('status', status))

    updater.start_polling()
    atexit.register(lambda: updater.stop())
