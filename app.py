from flask import Flask, request
from flask_restplus import Resource, Api
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, desc, func
from flask_marshmallow import Marshmallow
from marshmallow import Schema, fields, post_load, ValidationError
import secrets
from functools import wraps
import os
import ldap3
from datetime import datetime
from pyHS100 import SmartPlug
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from telegram.ext import Updater, CommandHandler

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

# Telegram config
updater = Updater('your_telegram_bot_token')

##################
##### Models #####
##################

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
    notify_email = db.Column(db.Boolean)
    notify_telegram = db.Column(db.Boolean)
    token = db.Column(db.String(255))
    telegram_chat_id = db.Column(db.Integer)
    telegram_token = db.Column(db.String(255))

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
        users = User.query.filter_by(notify_email=True)
        return user_list_schema.dumps(users)
    
    @jwt_required
    @api.doc(security='apikey')
    def post(self):
        id = get_jwt_identity()
        user = User.query.filter_by(id=id).first()
        user.notify_email = True
        db.session.commit()
        return { 'result': 'success', 'user_added': user.name }, 200

    @jwt_required
    @api.doc(security='apikey')
    def delete(self):
        id = get_jwt_identity()
        user = User.query.filter_by(id=id).first()
        user.notify_email = False
        db.session.commit()
        return { 'result': 'success', 'details': user.name + " won't be notified" }

@api.route('/notify/telegram')
class NotifyTelegram(Resource):
    @jwt_required
    @api.doc(security='apikey')
    def get(self):
        users = User.query.filter_by(notify_telegram=True)
        return user_list_schema.dumps(users)

    @jwt_required
    @api.doc(security='apikey')
    def post(self):
        id = get_jwt_identity()
        user = User.query.filter_by(id=id).first()
        user.telegram_token = secrets.token_urlsafe()
        db.session.commit()
        auth_url = "https://telegram.me/{}?start={}".format(updater.bot.name[1:], user.telegram_token)
        return { 'result': 'success', 'auth_url': auth_url }, 200

    @jwt_required
    @api.doc(security='apikey')
    def delete(self):
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

        # If user is already authenticated, reset.
        result = User.query.filter_by(username=username).first()
        if result:
            db.session.delete(result)
            db.session.flush()

        user = User(username=username,
                    email=conn.entries[0].mail.value,
                    name=conn.entries[0].name.value,
                    notify_email=False,
                    notify_telegram=False,
                    telegram_token = "",
                    telegram_chat_id=None,
                    token=None)
        db.session.add(user)
        db.session.flush() # Apply changes to database, but keep operation pending
        token = create_access_token(identity=user.id) # Use the primary key as token
        user.token = token # Save token in db
        db.session.commit() # Commit all transactions

        return token


#######################################
##### Update Washing Machine Data #####
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
        notify_all()
    

def notify_all():
    # Email
    users_email = User.query.filter_by(notify_email=True)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    
    msg = "The Washing Machine has just finished!"
    for user in users_email:
        server.sendmail(sender_email, user.email, msg)
        user.notify_email = False # Only notify once
    server.quit()        
    db.session.commit()

    # Telegram
    users_telegram = User.query.filter_by(notify_telegram=True)

    for user in users_telegram:
        updater.bot.send_message(chat_id=user.telegram_chat_id, text="The laundry is ready!")
        user.notify_telegram = False # Only notify once
    db.session.commit()

# Run update task in the background
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_washing_mashine, trigger="interval", seconds=5)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

####################
##### Telegram #####
####################

def telegram_auth_required(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        user = User.query.filter_by(telegram_chat_id=update.message.chat_id).first()
        if not user:
            update.message.reply_text("Unauthorized. Please authenticate first.")
            return

        return func(bot, update, *args, **kwargs)
    return wrapped

def start(bot, update, args):
    if not args:
        update.message.reply_text("Missing token. Please authenticate first.")
        return

    user = User.query.filter_by(telegram_token=args[0]).first()
    if not user:
        update.message.reply_text("Invalid token. Please authenticate first.")
        return

    user.telegram_chat_id = update.message.chat_id        
    db.session.commit()
    update.message.reply_text("Successfully authenticated!")

@telegram_auth_required
def notify(bot, update):
    user = User.query.filter_by(telegram_chat_id=update.message.chat_id).first()
    user.notify_telegram = True
    db.session.commit()

    update.message.reply_text("You will be notified as soon as the laundry is ready.")

@telegram_auth_required
def status(bot, update):
    washing_machine = WashingMachine.query.order_by(desc('timestamp')).first()
    update.message.reply_text("Running" if washing_machine.running else "Stopped") 

updater.dispatcher.add_handler(CommandHandler('notify', notify))
updater.dispatcher.add_handler(CommandHandler('start', start, pass_args=True))
updater.dispatcher.add_handler(CommandHandler('status', status))

updater.start_polling() # Looks like it blocks, when importing module in python idle
#updater.idle() # I don't think I need this, since the process is running anyway? (And polling ist in another thread)

# Shutdown the polling on exit
atexit.register(lambda: updater.stop())

if __name__ == '__main__':
    app.run(debug=True, user_reloader=false)