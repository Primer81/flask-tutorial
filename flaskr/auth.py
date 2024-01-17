import flask
import functools
import werkzeug.security
from flask import Blueprint, Response
from typing import Callable, Any
from sqlite3 import Connection, Row, Cursor

import flaskr.db

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view: Callable) -> Callable:
    @functools.wraps(view)
    def wrapped_view(*args: Any, **kwargs: Any) -> Any:
        if flask.g.user is None:
            url_login: str = flask.url_for("auth.login")
            return flask.redirect(url_login)
        return view(*args, **kwargs)
    return wrapped_view


@bp.before_app_request
def load_logged_in_user() -> None:
    user_id = flask.session.get("user_id")
    if user_id is None:
        flask.g.user = None
    else:
        db: Connection = flaskr.db.get_db()
        sql: str = "SELECT * FROM user WHERE id = ?"
        sql_params: tuple = (user_id,)
        users: Cursor = db.execute(sql, sql_params)
        user: Row | None = users.fetchone()
        flask.g.user = user


@bp.route("/logout")
def logout() -> Response:
    flask.session.clear()
    url_index: str = flask.url_for("index")
    return flask.redirect(url_index)


@bp.route("/register", methods=("GET", "POST"))
def register() -> str | Response:
    """Handle registration requests"""
    result: str | Response | None = None
    if flask.request.method == "POST":
        result = register_post()
    if result is None:
        result = register_get()
    return result


def register_get() -> str:
    """Return registration HTML page"""
    return flask.render_template("auth/register.html")


def register_post() -> Response | None:
    """Handle user submitted registration form"""
    result: Response | None = None
    username: str = flask.request.form["username"]
    password: str = flask.request.form["password"]
    error: str | None = None

    if not username:
        error = "Username is required."
    elif not password:
        error = "Password is required."

    if error is None:
        error = register_add_user(username, password)

    if error is None:
        url_login: str = flask.url_for("auth.login")
        result = flask.redirect(url_login)

    if error is not None:
        flask.flash(error)

    return result


def register_add_user(username: str, password: str) -> str | None:
    """Add a new user into the database"""
    error: str | None = None
    db: Connection = flaskr.db.get_db()
    password_hash: str = werkzeug.security.generate_password_hash(password)
    sql: str = "INSERT INTO user (username, password) VALUES (?, ?)"
    sql_params: tuple = (username, password_hash)
    try:
        db.execute(sql, sql_params)
        db.commit()
    except db.IntegrityError:
        error = f"User {username} is already registered."
    return error


@bp.route("/login", methods=("GET", "POST"))
def login() -> str | Response | None:
    """Handle login requests"""
    result: str | Response | None
    if flask.request.method != "POST":
        result = login_get()
    else:
        result = login_post()
    return result


def login_get() -> str:
    """Return login HTML page"""
    return flask.render_template('auth/login.html')


def login_post() -> Response | None:
    """Handle user submitted login form"""
    result: Response | None = None
    username: str = flask.request.form['username']
    password: str = flask.request.form['password']

    error: str | None
    user: Row | None
    error, user = login_fetch_user(username, password)

    if error is None:
        flask.session.clear()
        flask.session["user_id"] = user["id"]
        url_index: str = flask.url_for("index")
        result = flask.redirect(url_index)

    if error is not None:
        flask.flash(error)

    return result


def login_fetch_user(username: str, password: str) -> tuple[str | None, Row | None]:
    error: str | None = None
    sql: str = "SELECT * FROM user WHERE username = ?"
    sql_params: tuple = (username,)
    db: Connection = flaskr.db.get_db()
    users: Cursor = db.execute(sql, sql_params)
    user: Row | None = users.fetchone()
    if user is None:
        error = "Incorrect username."
    elif not werkzeug.security.check_password_hash(user["password"], password):
        error = "Incorrect password."
    return error, user
