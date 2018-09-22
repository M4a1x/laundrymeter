from sqlalchemy import asc, desc, func
from pyHS100 import SmartPlug
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import smtplib
import atexit

from .models import User, WashingMachine, db


def notify_all():
    # Email
    users_email = User.query.filter_by(notify_email=True)

    if users_email:
        with smtplib.SMTP_SSL('smtp.gmail.com', 587) as server:
            server.login(app.config['SMTP_EMAIL'], app.config['SMTP_PASSWORD'])
            
            msg = 'Subject: {}\n\n{}'.format(
                "The laundry is ready!",
                "The time was: {}.\n\n---\nThis service has been kindly provided by your friendly neighbourhood programmer.".format(datetime.now))
            for user in users_email:
                server.sendmail(app.config['SMTP_EMAIL'], user.email, msg)
                user.notify_email = False # Only notify once     
            db.session.commit()

    # Telegram
    users_telegram = User.query.filter_by(notify_telegram=True)

    if users_telegram:
        for user in users_telegram:
            updater.bot.send_message(chat_id=user.telegram_chat_id, text="The laundry is ready!")
            user.notify_telegram = False # Only notify once
        db.session.commit()


def update_washing_mashine():
    with app.app_context():
        now = datetime.utcnow()
        last = None

        # Try to get a reading. If it fails, enter default values into the database.
        try:
            # TODO: Log when no connection.
            emeter = plug.get_emeter_realtime()
            running = emeter['power_mw']/1000 > 5 # Drawing more than 5W means the machine is running... TODO: get actual value!
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
        except:
            washing_machine = WashingMachine(timestamp=now,
                                            running=False,
                                            last_changed=None,
                                            voltage=0,
                                            current=0,
                                            power=0,
                                            total_power=0)

        db.session.add(washing_machine)
        db.session.flush()

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
    global app
    app = flask_app

    global plug
    plug = SmartPlug(flask_app.config['SMART_PLUG_IP'])

    # Run update task in the background
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_washing_mashine, trigger="interval", seconds=flask_app.config['POLL_INTERVAL'])
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())