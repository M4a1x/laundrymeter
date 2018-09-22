from flask_restplus import Namespace, Resource
from sqlalchemy import desc

from ..models import WashingMachine, WashingMachineSchema
from .auth import auth


api = Namespace('machine',
                description='Operations for querying the current washing machine status.')

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
        washing_machine = WashingMachine.query.order_by(desc('timestamp')).first()
        return wm_status_schema.dumps(washing_machine) # dumps returns JSON, dump dic


@api.route('/debug')
class DebugInfo(Resource):
    @auth.login_required
    def get(self):
        "Return current extended status of the washing machine."
        washing_machine = WashingMachine.query.order_by(desc('timestamp')).first()
        return wm_debug_schema.dumps(washing_machine)

@api.route('/history/<int:amount>')
class MachineHistory(Resource):
    @auth.login_required
    def get(self, amount):
        "Returns list of last `amount` washing machine states (one state every 5s)."
        history = WashingMachine.query.order_by(desc('timestamp')).limit(amount)
        return wm_debug_schema.dumps(history, many=True)
