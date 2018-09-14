from flask import Blueprint
from flask_restplus import Api

from .machine import api as machine
from .email import api as email
from .telegram import api as telegram
from .auth import api as auth, auth as basic_auth

# Create Flask Blueprint
bp = Blueprint('api', __name__, url_prefix='/api')

# Document HTTP Basic Auth
authorizations = {
    'basicAuth': {
        'type': 'http',
    }
}

# TODO: Test if default 'decorators' work as expected
# Use the Blueprint for the main api
api = Api(bp,
    title='Washing Machine Service Api',
    version='0.1.0',
    description='Provides various endpoints and interfaces for getting the status of the Washing machine.',
    authorizations=authorizations,
    security='basicAuth' # Document authorization for all endpoints
    decorators=basic_auth.login_required # Require authorizations for all endpoints
    # All API metadatas
    # TODO: Input metadata defining the api
)

# Add api namespaces to the main api
api.add_namespace(machine, path='/machine')
api.add_namespace(auth, path='/auth')
api.add_namespace(email, path='/email')
api.add_namespace(telegram, path='/telegram')