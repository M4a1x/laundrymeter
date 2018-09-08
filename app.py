from flask import Flask
from flask_restplus import Resource, Api
from flask_jwt_extended import (JWTManager, jwt_required, get_jwt_identity,
    create_access_token)
from marshmallow import Schema, fields, post_load, ValidationError
import ldap3
from datetime import datetime

# We're building a flask api
app = Flask(__name__)

# Register RESTplus plugin
api = Api(app, prefix="/api")

# Register JWT-extended plugin
app.config['JWT_SECRET_KEY'] = 'super-secret' # TODO: Create secret
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False # Tokens live forever, for now.
jwt = JWTManager(app)

##################
##### Models #####
##################

class User(object):
    def __init__(self, username, name="", email="", password=""):
        self.username = username
        self.password = password
        self.email = email
        self.name = name


class WashingMachine(object):
    def __init__(self):
        self.running = False
        self.last_changed = datetime.now()
        self.voltage = 0
        self.current = 0
        self.power = 0
        self.total_power = 0

washing_machine = WashingMachine()
notifyList = []
notifyList.append(User("hasselmann", name="Leonard Hasselmann", email="l.hasselmann@web.de"))

##################
##### Schema #####
##################

class WashingMachineSchema(Schema):
    class Meta:
        fields = ('running', 'last_changed',
                  'voltage', 'current', 'power', 'total_power')

washing_mashine_status_schema = WashingMachineSchema(only=('running', 'last_changed'))
washing_mashine_debug_schema = WashingMachineSchema()

class UserSchema(Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)

    @post_load
    def make_user(self, data):
        return User(**data)

class UserInfoSchema(Schema):
    username = fields.String(required=True)
    name = fields.String(required=True)
    email = fields.Email(required=True)

    @post_load
    def make_user(self, data):
        return User(**data)


user_list_schema = UserInfoSchema(only=['name'], many=True)
user_info_schema = UserInfoSchema()
user_schema = UserSchema()

#########################
##### API Functions #####
#########################

@api.route('/machine')
class Machine(Resource):
    @jwt_required
    def get(self):
        return washing_mashine_status_schema.dump(washing_machine)

@api.route('/machine/debug')
class DebugInfo(Resource):
    @jwt_required
    def get(self):
        return washing_mashine_debug_schema.dump(washing_machine)

@api.route('/notify')
class Notify(Resource):
    @jwt_required
    def get(self):
        return user_list_schema.dump(notifyList)
    
    @jwt_required
    def post(self):
        try:
            user = user_info_schema.load(get_jwt_identity())
            notifyList.append(user)
            return { 'result': 'success', 'user_added': user_info_schema.dump(user) }, 200
        except ValidationError as err:
            return { 'result': 'error', 'details': err.messages}, 400

    @jwt_required
    def delete(self):
        try:
            user = user_info_schema.load(get_jwt_identity())
            if user in notifyList:
                notifyList.remove(user)
            else:
                return { 'result': 'error', 'details': 'User not on notify list' }, 400
        except ValidationError as err:
            return { 'result': 'error', 'details': err.messages}, 400

###################################################
##### JWT Authentication and Identity Methods #####
###################################################

@api.route('/auth')
class Authentication(Resource):
    def post(self):
        try:
            user = user_schema.load(api.payload)
            server = ldap3.Server('ldap.example.org', use_ssl=True, get_info=ldap3.ALL)
            conn = ldap3.Connection(server, user.username + '@ldap.example.org', user.password)
            if conn.bind():
                resultSearch = conn.search('DC=ldap, DC=example, DC=org',
                                           '(&(sAMAccountName={username})(objectclass=person))'.format(username=user.username),
                                           attributes=['name', 'mail'])
                if not resultSearch:
                    return { 'result': 'error', 'details': 'LDAP search error'}, 400

                user.email = conn.entries[0].mail
                user.name = conn.entries[0].name
                return create_access_token(identity=user_info_schema.dump(user))
            else:
                return { 'result': 'error', 'details': 'LDAP authentication error'}, 401
        except ValidationError as err:
            return { 'result': 'error', 'details': err.messages}, 400

if __name__ == '__main__':
    app.run(debug=True)
