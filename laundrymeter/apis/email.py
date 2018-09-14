from flask_restplus import Namespace, Resource

from ..models import User, UserSchema
from .auth import auth


api = Namespace('email', description='Operations for registering and listing Email notifications.')

user_list_schema = UserSchema(only=['name'], many=True)
user_schema = UserSchema()


# TODO: Add failure.. (i.e. on error)
@api.route('/notify/email')
class NotifyEmail(Resource):
    def get(self):
        users = User.query.filter_by(notify_email=True)
        return user_list_schema.dumps(users), 200
    
    def post(self):
        g.user.register_notification(email=True)
        return { 'result': 'success', 'email_added': user.email }, 200

    def delete(self):
        g.user.register_notification(email=True)
        return { 'result': 'success', 'details': user.email + " won't recieve an email." }, 200
