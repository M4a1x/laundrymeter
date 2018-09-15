import click
from flask.cli import with_appcontext

from .models import db


# DB Helper functions
def init_app(app):
    """Register the 'init-db' call for re-initializing the database.x"""
    app.cli.add_command(init_db_command)

def init_db():
    """Drop all tables in the database and create a new one."""
    db.reflect()
    db.drop_all()
    db.create_all()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')