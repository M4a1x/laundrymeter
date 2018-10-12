from sqlalchemy import asc, desc, func
from pyHS100 import SmartPlug, SmartDeviceException
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import smtplib
import atexit

from .models import User, WashingMachine, db
from . import telegram_bot as tb


def notify_all():
    # Email
    app.logger.debug('Notifying users by email...')
    try:
        users_email = User.query.filter_by(notify_email=True)
    except:
        app.logger.exception("There was an error querying users to be notified via email.")
        users_email = None

    if users_email:
        app.logger.debug('Trying to notify %d users via email.', len(users_email))
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            try:
                server.starttls() # Starts the connection
                server.login(app.config['SMTP_EMAIL'], app.config['SMTP_PASSWORD'])
                
                msg = 'Subject: {}\n\n{}'.format(
                    "The laundry is ready!",
                    "The time was: {}.\n\n\n---\nThis service is kindly provided by your friendly neighbourhood programmer.".format(datetime.now()))
                for user in users_email:
                    try:
                        server.sendmail(app.config['SMTP_EMAIL'], user.email, msg)
                        user.notify_email = False # Only notify once     
                    except smtplib.SMTPRecipientsRefused as e:
                        app.logger.excpetion("Recipient refused. Is the Email of user %s (%s) correct? %s", user.username, user.name, user.email)
                db.session.commit()
            except smtplib.SMTPHeloError as e:
                app.logger.exception("Couldn't start a connection with the SMTP server!")
            except smtplib.SMTPAuthenticationError as e:
                app.logger.exception("SMTP credentials are wrong! %s:%s", app.config['SMTP_EMAIL'], app.config['SMTP_PASSWORD'])
            except Exception as e:
                app.logger.exception("There was an unexpected exception while sending notification emails!")
    else:
        app.logger.debug('No user wanted to be notified via email.')

    # Telegram
    try:
        users_telegram = User.query.filter_by(notify_telegram=True)
    except Exception as e:
        app.logger.exception("There was an error querying users to be notified via telegram.")
        users_telegram = None

    if users_telegram:
        app.logger.debug("Trying to notify %d users via telegram...", len(users_telegram))
        for user in users_telegram:
            try:
                tb.updater.bot.send_message(chat_id=user.telegram_chat_id, text="The laundry is ready!")
                user.notify_telegram = False # Only notify once
            except:
                app.logger.exception("There was an error sending telegram notifications to %s (%s)!", user.username, user.name)
        try:
            db.session.commit()
        except:
            app.logger.exception("There was an error writing to the database.")
    else:
        app.logger.debug("No user wanted to be notified via telegram.")

def createEmptyWashingMachine(now):
    return WashingMachine(timestamp=now,
                          running=False,
                          last_changed=None,
                          voltage=0,
                          current=0,
                          power=0,
                          total_power=0)

def update_washing_mashine():
    with app.app_context():
        global counter
        global running
        now = datetime.utcnow()
        last = None

        # Try to get a reading. If it fails, enter default values into the database.
        try:
            # TODO: Log when no connection.
            app.logger.debug('Querying emeter of TP-Link Smartplug...')
            emeter = plug.get_emeter_realtime()
            app.logger.debug('Finished querying emeter: %s', emeter)
            if running:
                app.logger.debug("Washing Machine is thought as running...")
                if emeter['power_mw']/1000 < 50: # Threshold of 50W for running/idle
                    counter += 1
                    app.logger.debug("Washing Machine is not running at this very moment (Power below threshold). Increasing counter by 1. Current counter: %d", counter)
                else:
                    counter = 0
                    app.logger.debug("Washing Machine is running at this very moment (Power above threshold). Resetting counter: %d", counter)

                if counter > 48: # Washing machine inactive for more than 48 measurments (4 min)
                    counter = 0
                    running = False
                    app.logger.debug("Washing Machine was thought of running, but is actually turned off. Counter %d. Running %s.", counter, running)
                
            else:
                app.logger.debug("Washing Machine is thought of as turned off...")
                if emeter['power_mw']/1000 > 50:
                    running = True
                    app.logger.debug("Washing Machine was thought of as turned off, but is actually running. Running %s", running)
                else:
                    app.logger.debug("Washing machine is off at this very moment (Power below threshold).")

            last = WashingMachine.query.order_by(desc('timestamp')).first()
            if last and last.running == running and last.last_changed:
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
            app.logger.debug("Successfully added emeter measurement to the database.")

        except SmartDeviceException as e:
            if e.args and e.args[0] == 'Communication error':
                app.logger.error("Couldn't connect to TP-Link Smartplug on %s", app.config['SMART_PLUG_IP'])
            else:
                app.logger.exception('Error querying the emeter of the TP-Link Smartplug.')
            washing_machine = createEmptyWashingMachine(now)

        except Exception as e:
            app.logger.exception('Error adding emeter measurement to the database.')
            washing_machine = createEmptyWashingMachine(now)

        # Restrict size of db
        count = db.session.query(func.count(WashingMachine.timestamp)).scalar()

        if count > 6307200: # delete oldest, when limit (one year; 6.307.200 rows (5sec interval), 50MB?) is reached
            washing_machine = WashingMachine.query.order_by(asc('timestamp')).first()
            db.session.delete(washing_machine)
        
        if count > 6400000: # Just to be sure..?
            db.session.query(WashingMachine).delete()

        db.session.commit()

        # Notify when Washing Mashine is finished
        if last and last.running == True != running:
            notify_all()

def init_app(flask_app):
    flask_app.logger.debug("Setting up wm_poller...")
    global app
    app = flask_app

    global plug
    plug = SmartPlug(flask_app.config['SMART_PLUG_IP'])

    global counter
    counter = 0

    global running
    running = False

    # Run update task in the background
    # TODO: Run this only once, even when run with multiple worker threads in gunicorn
    flask_app.logger.debug("Starting wm_poller background task...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_washing_mashine, trigger="interval", seconds=flask_app.config['POLL_INTERVAL'])
    scheduler.start()
    flask_app.logger.debug("Started wm_poller background task.")

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    flask_app.logger.debug("Setup wm_poller.")