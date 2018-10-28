import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from plotly import graph_objs as go

import flask
from flask import g
import base64
from sqlalchemy import desc

from .models import WashingMachine
from .apis.auth import auth

def update_metrics(n):
    return [ html.Span(n) ]

def generate_figure(n, relayoutData):
    with app.server.app_context():
        history = WashingMachine.query.with_entities(WashingMachine.timestamp, WashingMachine.current, WashingMachine.running).order_by(desc('timestamp')).limit(2160).all() # 1 day
        (x_axis, current_list, status_list) = zip(*history)
        status_list = [stat * 10 for stat in status_list]
        current = go.Scatter(x=x_axis, y=current_list, name="Current [A]")
        status = go.Scatter(x=x_axis, y=status_list, name="Status [on/off]")
        if(relayoutData and 'xaxis.range[0]' in relayoutData and 'yaxis.range[0]' in relayoutData):
            layout = go.Layout(
                title="Washing Machine Status",
                xaxis=dict(
                    range=[relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']]
                ), 
                yaxis=dict(
                    range=[relayoutData['yaxis.range[0]'], relayoutData['yaxis.range[1]']]
                    )
            )
        else:
            layout = go.Layout(title="Washing Machine Status")
        figure = go.Figure(data=[current, status], layout=layout)
        return figure

def serve_layout():
    figure = generate_figure(-1, None)
    layout = html.Div([
        html.Div(id='live-update-text'),
        html.H1('Welcome to Laundrymeter!'),
        html.P('Press the buttons below to be notified when the laundry is ready.'),
        html.Div([
            html.Button('Notify via E-Mail.', id='button-email'),
            html.Button('Notify via Telegram.', id='button-telegram')
        ], id='div-button'),
        dcc.Graph(id='laundrymeter-graph', figure=figure),
        dcc.Interval(
            id='interval-component',
            interval=app.server.config['POLL_INTERVAL']*10 * 1000, # interval is in milliseconds
            n_intervals=0
        )
    ], style={'text-align': 'center'})
    return layout

def notify_email(n):
    if n is None: # Page Load
        if g.user.notify_email:
            return "You will be notified via E-Mail. Remove?"
        else:
            return "Notify via E-Mail."
    else:
        if not g.user.notify_email:
            g.user.register_notification(email=True)
            return "You will be notified via E-Mail. Remove?"
        else:
            g.user.register_notification(email=False)
            return "Notify via E-Mail."

def notify_telegram(n):
    if n is None: # Page Load
        if g.user.notify_telegram:
            return "You will be notified via Telegram. Remove?"
        else:
            return "Notify via Telegram."
    else:
        if not g.user.notify_telegram:
            g.user.register_notification(telegram=True)
            return "You will be notified via Telegram. Remove?"
        else:
            g.user.register_notification(telegram=False)
            return "Notify via Telegram."

def is_authorized(self):
    header = flask.request.headers.get('Authorization', None)
    if not header:
        return False
    username_password = base64.b64decode(header.split('Basic ')[1])
    username_password_utf8 = username_password.decode('utf-8')
    username, password = username_password_utf8.split(':')
    return auth.verify_password_callback(username, password)

def init_app(flask_app):
    global app
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, server=flask_app, external_stylesheets=external_stylesheets)
    auth = dash_auth.BasicAuth(app, []) # Empty user list, because we monkey patch the auth funktion later
    dash_auth.BasicAuth.is_authorized = is_authorized # Monkeypatching for now. TODO: Find a cleaner solution!

    app.layout = serve_layout()

    global update_metrics
    update_metrics = app.callback(Output('live-update-text', 'children'),
                                  [Input('interval-component', 'n_intervals')])(update_metrics)
    
    global generate_figure
    generate_figure = app.callback(Output('laundrymeter-graph', 'figure'), 
                                   [Input('interval-component', 'n_intervals'),
                                    Input('laundrymeter-graph', 'relayoutData')])(generate_figure)

    global notify_email
    notify_email = app.callback(Output('button-email', 'children'),
                                [Input('button-email', 'n_clicks')])(notify_email)

    global notify_telegram
    notify_telegram = app.callback(Output('button-telegram', 'children'),
                                   [Input('button-telegram', 'n_clicks')])(notify_telegram)