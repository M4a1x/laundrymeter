from flask import g, current_app
from flask_restplus import Namespace, Resource, abort
from sqlalchemy import desc

from ..models import WashingMachine, WashingMachineSchema
from .auth import auth


api = Namespace('machine',
                description='Operations for querying the current machine status.')

wm_status_schema = WashingMachineSchema(only=('timestamp', 'running', 'last_changed'))
wm_debug_schema = WashingMachineSchema()

# TODO: Check returned Schema format. Maybe include name/title?
# TODO: Add api doc
# TODO: Add docstring

@api.route('/')
class Machine(Resource):
    @auth.login_required
    def get(self):
        "Return the current status of the washing machine."
        try:
            washing_machine = WashingMachine.query.order_by(desc('timestamp')).first()
        except Exception as e:
            current_app.logger.exception('User %s (%s) raised an error on get()', g.user.username, g.user.name)
            return abort(500)
        
        current_app.logger.debug('User %s (%s) successfully called get()', g.user.username, g.user.name)
        return wm_status_schema.dumps(washing_machine) # dumps returns JSON, dump dic


@api.route('/debug')
class DebugInfo(Resource):
    @auth.login_required
    def get(self):
        "Return current extended status of the washing machine."
        try:
            washing_machine = WashingMachine.query.order_by(desc('timestamp')).first()
        except Exception as e:
            current_app.logger.exception('User %s (%s) raised an error on get()', g.user.username, g.user.name)
            return abort(500)

        current_app.logger.debug('User %s (%s) successfully called get()', g.user.username, g.user.name)
        return wm_debug_schema.dumps(washing_machine)

@api.route('/history/<int:amount>')
class MachineHistory(Resource):
    @auth.login_required
    def get(self, amount):
        "Returns list of last 'amount' washing machine states (one state every 5s)."
        try:
            history = WashingMachine.query.order_by(desc('timestamp')).limit(amount)
        except Exception as e:
            current_app.logger.exception('User %s (%s) raised an error on get(%d)', g.user.username, g.user.name, amount)
            return abort(500)

        current_app.logger.debug('User %s (%s) successfully called get(%d)', g.user.username, g.user.name)
        return wm_debug_schema.dumps(history, many=True)
