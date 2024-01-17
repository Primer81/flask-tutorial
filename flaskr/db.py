import click
import flask
import sqlite3
from flask import Flask
from typing import Optional
from sqlite3 import Connection, Row


def init_app(app: Flask):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def init_db() -> None:
    db: Connection = get_db()
    with flask.current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf-8'))


@click.command('init-db')
def init_db_command() -> None:
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def get_db() -> Connection:
    if 'db' not in flask.g:
        db: Connection = sqlite3.connect(
            flask.current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        db.row_factory = Row
        flask.g.db = db
    return flask.g.db


def close_db(_=None) -> None:
    db: Optional[Connection] = flask.g.pop('db', None)
    if db is not None:
        db.close()
