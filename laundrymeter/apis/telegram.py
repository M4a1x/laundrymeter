from flask import g
from flask_restplus import Namespace, Resource

from ..models import User, UserSchema
from .auth import auth
from .. import telegram_bot


api = Namespace('telegram',
                description='Operations for registering and listing Telegram notifications.')

user_list_schema = UserSchema(only=['name'], many=True)


@api.route('/')
class NotifyTelegram(Resource):
    @auth.login_required
    def get(self):
        """Get a list of users to be notified via telegram."""
        users = User.query.filter_by(notify_telegram=True)
        return user_list_schema.dumps(users)

    @auth.login_required
    def post(self):
        """Add own user to be notified via email."""
        if g.user.telegram_chat_id:
            g.user.register_notification(telegram=True)
            return { 'result': 'success', 'notify_telegram': g.user.name }, 200
        else:
            return { 'result': 'failure', 'details': 'Please register telegram first.' }, 400

    @auth.login_required
    def delete(self):
        """Remove own user to be notifed via email."""
        if g.user.telegram_chat_id:
            g.user.register_notification(telegram=False)
            return { 'result': 'success', 'details': g.user.name + " won't recieve a message via telegram." }, 200
        else:
            return { 'result': 'failure', 'details': 'Please register telegram first.' }, 400


@api.route('/register')
class RegisterTelegram(Resource):
    @auth.login_required
    def post(self):
        """Register own user to enable notification via telegram. Replaces old user if previously registered."""
        token = g.user.generate_telegram_token()
        auth_url = "https://telegram.me/{}?start={}".format(telegram_bot.updater.bot.name[1:], token)
        return { 'result': 'success', 'auth_url': auth_url }, 200