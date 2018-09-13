# -*- coding: utf-8 -*-
"""Operations for authentication

This module contains functions for authentication. Namely a function for
verifying logins and an api endpoint for generating tokens. Simply import
`auth` from here and protect any function called with `@auth.login_required`.
Authentication is possible via username:password or token:unused via 
HTTP Basic Auth. 

"""

from flask_restplus import Namespace, Resource
from flask_httpauth import HTTPBasicAuth
from flask import current_app, g
from ..models import User, db


api = Namespace('auth', description='Operations for authentication.')
auth = HTTPBasicAuth()

@api.route('/')
class Authentication(Resource):
    @api.doc('get_token')
    @auth.login_required
    def get(self):
        '''Get a new token and invalidate the old one if it exists.'''
        token = g.user.generate_auth_token()
        return { 'token': token }


@auth.verify_password
def verify_login(username_or_token, password):
    '''Verify username/password or token and return corresponding User object.

    Token can be obtained from the auth resource.

    Args:
        username_or_token: The token or username to verify.
                           Supplied via Basic HTTP.
        password: Correspondig password. Only checked if no token was supplied.

    Returns:
        True on valid login, false otherwise.
        Corresponding User object is stored in `g.user`.
    
    '''
    user = User.verify_auth_token(username_or_token)
    if not user:
        # Verify User against ldap
        server = ldap3.Server(current_app.config['LDAP_URL'],
                              use_ssl=True,
                              get_info=ldap3.ALL)
        conn = ldap3.Connection(server, 
                                '{username}@{ldap}'.format(
                                    username=username_or_token,
                                    ldap=current_app.config['LDAP_URL']),
                                password)
        if not conn.bind():
            return False

        # Check if user is in local database already
        user = User.query.get(username_or_token)

        # Add new record if not
        if not user:
            resultSearch = conn.search(
                    current_app.config['LDAP_BASE_DN'],
                    '(&(sAMAccountName={username})(objectclass=person))'.format(
                        username=username_or_token),
                    attributes=['name', 'mail'])
            if not resultSearch:
                return False

            user = User(username=username,
                        email=conn.entries[0].mail.value,
                        name=conn.entries[0].name.value,
                        notify_email=False,
                        notify_telegram=False,
                        telegram_token = "",
                        telegram_chat_id=None,
                        auth_token=None)
            db.session.add(user)
            db.session.commit()

    # Add user to global context, so it is accessible in the called method
    g.user = user
    return True

    
