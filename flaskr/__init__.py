import os
from flask import Flask
from typing import Mapping, Any

import flaskr.db
import flaskr.auth
import flaskr.blog


def create_app(test_config: Mapping[str, Any] | None = None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    # TODO: update secret key to random value
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError as e:
        print(e)
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello World!'

    # initialize database with app
    flaskr.db.init_app(app)

    # initialize authentication blueprint
    app.register_blueprint(flaskr.auth.bp)

    # initialize blog blueprint
    app.register_blueprint(flaskr.blog.bp)
    app.add_url_rule('/', endpoint='index')

    return app
