from flask import g, current_app
from flask_restplus import Namespace, Resource, abort

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
        try:
            users = User.query.filter_by(notify_telegram=True)
        except Exception as e:
            current_app.logger.exception('User %s (%s) raised exception on get()', g.user.username, g.user.name)
            return abort(500)
        
        current_app.logger.debug('User %s (%s) successfully called get()', g.user.username, g.user.name)
        return user_list_schema.dumps(users)

    @auth.login_required
    def post(self):
        """Add own user to be notified via telegram."""
        if g.user.telegram_chat_id:
            try:
                g.user.register_notification(telegram=True)
            except Exception as e:
                current_app.logger.exception('User %s (%s) raised an exception on post()', g.user.username, g.user.name)
                return abort(500)
            current_app.logger.debug('User %s (%s) successfully called post()', g.user.username, g.user.name)
            return { 'result': 'success', 'notify_telegram': g.user.name }, 200
        else:
            current_app.logger.info('User %s (%s) tried to call post() without having registered telegram', g.user.username, g.user.name)
            return { 'result': 'failure', 'details': 'Please register telegram first.' }, 400

    @auth.login_required
    def delete(self):
        """Remove own user to be notifed via telegram."""
        if g.user.telegram_chat_id:
            try:
                g.user.register_notification(telegram=False)
            except Exception as e:
                current_app.logger.exception('User %s (%s) raised an exception on delete()', g.user.username, g.user.name)
                return abort(500)
            current_app.logger.debug('User %s (%s) successfully called delete()', g.user.username, g.user.name)
            return { 'result': 'success', 'details': g.user.name + " won't recieve a message via telegram." }, 200
        else:
            current_app.logger.info('User %s (%s) tried to call delete() without having registered telegram', g.user.username, g.user.name)
            return { 'result': 'failure', 'details': 'Please register telegram first.' }, 400


@api.route('/register')
class RegisterTelegram(Resource):
    @auth.login_required
    def post(self):
        """Register own user to enable notification via telegram.
        Replaces old user if previously registered, thus deauthenticating him."""
        try:
            token = g.user.generate_telegram_token()
            auth_url = "https://telegram.me/{}?start={}".format(telegram_bot.updater.bot.name[1:], token)
            current_app.logger.debug('User %s (%s) successfully called post(). Token added.', g.user.username, g.user.name)
            return { 'result': 'success', 'auth_url': auth_url }, 200
        except Exception as e:
            current_app.logger.exception("User %s (%s) raised an exception on post(). Token couldn't be added", g.user.username, g.user.name)
            return abort(500)