from flask import current_app
from sqlalchemy import asc, desc, func
from pyHS100 import SmartPlug
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import atexit

from models import User, WashingMachine, db


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


def update_washing_mashine():
    now = datetime.utcnow()

    # Try to get a reading. If it fails, enter default values into the database.
    try:
        # TODO: Log when no connection.
        emeter = plug.get_emeter_realtime()
        running = emeter['power_mw']/1000 > 10 # Drawing more than 10W means the machine is running... TODO: get actual value!
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


def init_app():
    # Run update task in the background
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_washing_mashine, trigger="interval", seconds=current_app.config['POLL_INTERVAL'])
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
