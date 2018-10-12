# -*- coding: utf-8 -*-
"""Operations for authentication

This module contains functions for authentication. Namely a function for
verifying logins and an api endpoint for generating tokens. Simply import
`auth` from here and protect any function called with `@auth.login_required`.
Authentication is possible via username:password or token:unused via 
HTTP Basic Auth. 

"""

from flask_restplus import Namespace, Resource, abort
from flask_httpauth import HTTPBasicAuth
from flask import current_app, g
from ldap3 import Server, Connection, ALL

from ..models import User, db

# TODO: Add api doc?


auth = HTTPBasicAuth()
api = Namespace('auth',
                description='Operations for authentication.')


@api.route('/')
class Authentication(Resource):
    @auth.login_required
    @api.doc('get_token')
    def get(self):
        """Get a new token and invalidate the old one if it exists.

        Use HTTP Basic Auth with `username:password` or `returned_token:unused`.

        Remember that the request should be base64 encoded:
        `Authorization: Basic base64('username:password')`
        """

        try:
            token = g.user.generate_auth_token()
        except Exception as e:
            current_app.logger.error('User {} ({}) could not generate token.', g.user.username, g.user.name, exc_info=True)
            return abort(500)

        current_app.logger.debug('User {} successfully created token {}', g.user.username, token)
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
    if not username_or_token:
        return False

    current_app.logger.debug('Starting user verification...')
    user = User.verify_auth_token(username_or_token)

    if user:
        current_app.logger.debug('User %s (%s) authenticated via token.', user.username, user.name)

    if not user:
        # Verify User against ldap
        server = Server(current_app.config['LDAP_URL'],
                        use_ssl=True,
                        get_info=ALL)
        ldap_username = '{username}@{ldap}'.format(username=username_or_token,
                                                   ldap=current_app.config['LDAP_URL'])
        conn = Connection(server, ldap_username, password)
        if not conn.bind():
            current_app.logger.debug('User %s could not be verified against LDAP.', username_or_token)
            return False

        # Check if user is in local database already
        user = User.query.get(username_or_token)

        if user:
            current_app.logger.debug('User %s (%s) authenticated via ldap.', user.username, user.name)

        # Add new record if not
        if not user:
            resultSearch = conn.search(
                    current_app.config['LDAP_BASE_DN'],
                    '(&(sAMAccountName={username})(objectclass=person))'.format(
                        username=username_or_token),
                    attributes=['name', 'mail'])
            if not resultSearch:
                current_app.logger.error('Could not get user info for %s from ldap.', username_or_token)
                return False

            user = User(username=username_or_token,
                        email=conn.entries[0].mail.value,
                        name=conn.entries[0].name.value,
                        notify_email=False,
                        notify_telegram=False,
                        telegram_token = None,
                        telegram_chat_id=None,
                        auth_token=None)
            current_app.logger.debug('New user %s (%s) has been created.', user.username, user.name)
            current_app.logger.debug('Trying to add new user %s (%s) to the database.', user.username, user.name)
            
            try:
                db.session.add(user)
                db.session.commit()
                current_app.logger.info('New user %s (%s) has been successfully added to the database.', user.username, user.name)
            except Exception as e:
                current_app.logger.exception("Couldn't add user %s (%s) to the database!", user.username, user.name)
                return False


    # Add user to global context, so it is accessible in the called method
    g.user = user
    return True

    
