from flask import Flask, request
from flask_restplus import Resource, Api
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, desc, func
from flask_marshmallow import Marshmallow
from marshmallow import Schema, fields, post_load, ValidationError
import os
import ldap3
from datetime import datetime
from pyHS100 import SmartPlug
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib

# TODO: Swagger documentation with RESTplus
# We're building a flask api
app = Flask(__name__)

# For documentation
authorizations = {
    'apikey': {
        'description': "The JWT Token, in the format: 'Bearer xxx.yyy.zzz'",
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}

# Register RESTplus plugin
api = Api(app, prefix="/api", authorizations=authorizations)

# Register JWT-extended plugin
app.config['JWT_SECRET_KEY'] = 'super-secret' # TODO: Create secret
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False # Tokens live forever, for now.
jwt = JWTManager(app)

# Register SQLAlchemy (before Marshmallow)
basedir = app.root_path # Maybe change this to app.instance_path later?
app.config['SQLALCHEMY_DATABASE_URI'] =  'sqlite:///' + os.path.join(basedir, 'app.db')
db = SQLAlchemy(app)

# Register Marshmallow
ma = Marshmallow(app)

# Set ip of plug
plug = SmartPlug("192.168.178.124")

# Email config
sender_email = "yoursenderemail@example.org"
sender_password = "your_smtp_password"

##################
##### Models #####
##################

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
    notifyEmail = db.Column(db.Boolean)
    notifyTelegram = db.Column(db.Boolean)
    token = db.Column(db.String(255))
    telegram_chat_id = db.Column(db.Integer)

class WashingMachine(db.Model):
    __tablename__ = 'washingmachine'
    timestamp = db.Column(db.DateTime, primary_key=True)
    running = db.Column(db.Boolean)
    last_changed = db.Column(db.DateTime)
    voltage = db.Column(db.Float)
    current = db.Column(db.Float)
    power = db.Column(db.Float)
    total_power = db.Column(db.Float)


##################
##### Schema #####
##################

class WashingMachineSchema(ma.ModelSchema):
    class Meta:
        model = WashingMachine

washing_machine_status_schema = WashingMachineSchema(only=('timestamp', 'running', 'last_changed'))
washing_machine_debug_schema = WashingMachineSchema()

class UserSchema(ma.ModelSchema):
    class Meta:
        model = User

    @post_load
    def make_user(self, data):
        return User(**data)


user_list_schema = UserSchema(only=['name'], many=True)
user_schema = UserSchema()


def converter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

#########################
##### API Functions #####
#########################

@api.route('/machine')
class Machine(Resource):
    @jwt_required
    @api.doc(security='apikey')
    def get(self):
        washing_machine = WashingMachine.query.order_by(desc('timestamp')).first()
        return washing_machine_status_schema.dumps(washing_machine) # dumps returns JSON, dump dic

@api.route('/machine/debug')
class DebugInfo(Resource):
    @jwt_required
    @api.doc(security='apikey')
    def get(self):
        washing_machine = WashingMachine.query.order_by(desc('timestamp')).first()
        return washing_machine_debug_schema.dumps(washing_machine)

@api.route('/notify/email')
class NotifyEmail(Resource):
    @jwt_required
    @api.doc(security='apikey')
    def get(self):
        users = User.query.filter_by(notifyEmail=True)
        return user_list_schema.dumps(users)
    
    @jwt_required
    @api.doc(security='apikey')
    def post(self):
        id = get_jwt_identity()
        user = User.query.filter_by(id=id).first()
        user.notifyEmail = True
        db.session.commit()
        return { 'result': 'success', 'user_added': user_schema.dumps(user) }, 200

    @jwt_required
    @api.doc(security='apikey')
    def delete(self):
        id = get_jwt_identity()
        user = User.query.filter_by(id=id).first()
        user.notifyEmail = False
        db.session.commit()
        return { 'result': 'success', 'details': "User won't be notified" }

@api.route('/notify/telegram') # TODO
class NotifyTelegram(Resource):
    @jwt_required
    @api.doc(security='apikey')
    def post(self):
        return

###################################################
##### JWT Authentication and Identity Methods #####
###################################################

# Authorization endpoint
@api.route('/auth')
@api.doc(security=None)
class Authentication(Resource):
    def post(self):
        username = api.payload['username']
        password = api.payload['password']
        server = ldap3.Server('ldap.example.org', use_ssl=True, get_info=ldap3.ALL)
        conn = ldap3.Connection(server, username + '@ldap.example.org', password)
        if not conn.bind():
            return { 'result': 'error', 'details': 'LDAP authentication error'}, 401

        resultSearch = conn.search('DC=ldap, DC=example, DC=org',
                                    '(&(sAMAccountName={username})(objectclass=person))'.format(username=username),
                                    attributes=['name', 'mail'])
        if not resultSearch:
            return { 'result': 'error', 'details': 'LDAP search error'}, 400

        user = User(username=username,
                    email=conn.entries[0].mail.value,
                    name=conn.entries[0].name.value,
                    notifyEmail=False,
                    notifyTelegram=False,
                    telegram_chat_id=None,
                    token=None)
        db.session.add(user)
        db.session.flush() # Apply changes to database, but keep operation pending
        token = create_access_token(identity=user.id) # Use the primary key as token
        user.token = token # Save token in db
        db.session.commit() # Commit all transactions

        return token


#######################################
##### Update Washing Mashine Data #####
#######################################

def update_washing_mashine():
    emeter = plug.get_emeter_realtime()
    now = datetime.utcnow()
    running = emeter['power_mw']/1000 > 5 # Drawing more than 10W means the machine is running... TODO: get actual values!
    last = WashingMachine.query.order_by(desc('timestamp')).first()
    if last and last.running == running:
        last_changed = last.last_changed
    else:
        last_changed = now

    washing_machine = WashingMachine(timestamp=now,
                                     running=running,
                                     last_changed=last_changed,
                                     voltage=emeter['voltage_mv']/1000,
                                     current=emeter['current_ma']/1000,
                                     power=emeter['power_mw']/1000,
                                     total_power=emeter['total_wh']/1000)
    
    db.session.add(washing_machine)
    db.session.flush()

    count = db.session.query(func.count(WashingMachine.timestamp)).scalar()

    if count > 6307200: # delete oldest, when limit (one year; 6.307.200 rows (5sec interval), 50MB?) is reached
        washing_machine = WashingMachine.query.order_by(asc('timestamp')).first()
        db.session.delete(washing_machine)
    
    if count > 6400000:
        db.session.query(WashingMachine).delete()

    db.session.commit()

    # Notify when Washing Mashine is finished
    if last and last.running == True != running:
        notify()
    

def notify():
    # Email
    users = User.query.filter_by(notifyEmail=True)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    
    msg = "The Washing Machine has just finished!"
    for user in users:
        server.sendmail(sender_email, user.email, msg)
        user.notifyEmail = False # Only notify once
    server.quit()        
    db.session.commit()

    # TODO: Telegram

# Run update task in the background
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_washing_mashine, trigger="interval", seconds=5)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(debug=True, user_reloader=false)