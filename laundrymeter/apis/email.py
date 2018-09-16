from flask import g
from flask_restplus import Namespace, Resource

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
        users = User.query.filter_by(notify_email=True)
        return user_list_schema.dumps(users), 200
    
    @auth.login_required
    def post(self):
        """Add own user to be notified via email."""
        g.user.register_notification(email=True)
        return { 'result': 'success', 'notify_email': g.user.email }, 200

    @auth.login_required
    def delete(self):
        """Remove own user to be notified via email."""
        g.user.register_notification(email=False)
        return { 'result': 'success', 'details': g.user.email + " won't recieve an email." }, 200
