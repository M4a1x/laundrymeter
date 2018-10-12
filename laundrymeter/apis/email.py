from flask import g, current_app
from flask_restplus import Namespace, Resource, abort

from ..models import User, UserSchema
from .auth import auth


api = Namespace('email',
                description='Operations for registering and listing Email notifications.')

user_list_schema = UserSchema(only=['name'], many=True)

# TODO: Add failure.. (i.e. on error)
# TODO: Add api doc
# TODO: Add docstring


@api.route('/')
class NotifyEmail(Resource):
    @auth.login_required
    def get(self):
        """Get a list of users to be notified via email."""
        try:
            users = User.query.filter_by(notify_email=True)
        except Exception as e:
            current_app.logger.exception('User %s (%s) raised an error on NotifyEmail.get()', g.user.username, g.user.name)
            return abort(500)
            
        current_app.logger.debug('User %s (%s) successfully called NotifyEmail.get()', g.user.username, g.user.name)
        return user_list_schema.dumps(users), 200
    
    @auth.login_required
    def post(self):
        """Add own user to be notified via email."""
        try:
            g.user.register_notification(email=True)
        except Exception as e:
            current_app.logger.exception('User %s (%s) raised an error on NotifyEmail.post()', g.user.username, g.user.name)
            return abort(500)

        current_app.logger.debug('User %s (%s) successfully called NotifyEmail.post()', g.user.username, g.user.name)
        return { 'result': 'success', 'notify_email': g.user.email }, 200

    @auth.login_required
    def delete(self):
        """Remove own user to be notified via email."""
        try:
            g.user.register_notification(email=False)
        except Exception as e:
            current_app.logger.exception('User %s (%s) raised an error on NotifyEmail.delete()', g.user.username, g.user.name)
            return abort(500)
        
        current_app.logger.debug('User %s (%s) successfully called NotifyEmail.delete()', g.user.username, g.user.name)
        return { 'result': 'success', 'message': g.user.email + " won't recieve an email." }, 200
