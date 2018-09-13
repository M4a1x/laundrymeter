from flask import Blueprint
from flask_restplus import Api

from .email import api as email
from .telegram import api as telegram
from .auth import api as auth

# Create Flask Blueprint
bp = Blueprint('api', __name__, url_prefix='/api')

# Use the Blueprint for the main api
api = Api(bp,
    title='Washing Machine Service Api',
    version='0.1.0',
    description='Provides various endpoints and interfaces for getting the status of the Washing machine.',
    # All API metadatas
    # TODO: Input metadata defining the api
)

# Add api namespaces to the main api
api.add_namespace(auth, path='/auth')
api.add_namespace(email, path='/email')
api.add_namespace(telegram, path='/telegram')