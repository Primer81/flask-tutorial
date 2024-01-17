import flask
from flask import Blueprint, Response
from sqlite3 import Connection, Cursor, Row
from werkzeug import exceptions

import flaskr.db
import flaskr.auth

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    db: Connection = flaskr.db.get_db()
    posts: list[Row] = db.execute(
        "SELECT p.id, title, body, created, author_id, username"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    return flask.render_template("blog/index.html", posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@flaskr.auth.login_required
def create() -> str | Response:
    if flask.request.method == 'POST':
        title = flask.request.form['title']
        body = flask.request.form['body']
        error: str | None = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flask.flash(error)
        else:
            db: Connection = flaskr.db.get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, flask.g.user['id'])
            )
            db.commit()
            return flask.redirect(flask.url_for('blog.index'))

    return flask.render_template('blog/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@flaskr.auth.login_required
def update(post_id: int):
    post = get_post(post_id)

    if flask.request.method == 'POST':
        title = flask.request.form['title']
        body = flask.request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flask.flash(error)
        else:
            db = flaskr.db.get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, post_id)
            )
            db.commit()
            return flask.redirect(flask.url_for('blog.index'))

    return flask.render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@flaskr.auth.login_required
def delete(post_id: int):
    get_post(post_id)
    db = flaskr.db.get_db()
    db.execute('DELETE FROM post WHERE id = ?', (post_id,))
    db.commit()
    return flask.redirect(flask.url_for('blog.index'))


def get_post(post_id: int, check_author=True):
    sql: str = ("SELECT p.id, title, body, created, author_id, username"
                " FROM post p JOIN user u ON p.author_id = u.id"
                " WHERE p.id = ?")
    sql_params: tuple = (post_id,)
    db: Connection = flaskr.db.get_db()
    results: Cursor = db.execute(sql, sql_params)
    post: Row = results.fetchone()

    if post is None:
        exceptions.abort(404, f"Post id {post_id} doesn't exist.")

    if check_author and post['author_id'] != flask.g.user['id']:
        exceptions.abort(403)

    return post
