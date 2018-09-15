from flask_restplus import Namespace, Resource
from sqlalchemy import desc

from ..models import WashingMachine, WashingMachineSchema
from .auth import auth


api = Namespace('machine', description='Operations for querying the current washing machine status.')

wm_status_schema = WashingMachineSchema(only=('timestamp', 'running', 'last_changed'))
wm_debug_schema = WashingMachineSchema()

# TODO: Check returned Schema format. Maybe include name/title?
# TODO: Add api doc
# TODO: Add docstring

@api.route('/machine')
class Machine(Resource):
    def get(self):
        washing_machine = WashingMachine.query.order_by(desc('timestamp')).first()
        return wm_status_schema.dumps(washing_machine) # dumps returns JSON, dump dic


@api.route('/machine/debug')
class DebugInfo(Resource):
    def get(self):
        washing_machine = WashingMachine.query.order_by(desc('timestamp')).first()
        return wm_debug_schema.dumps(washing_machine)
