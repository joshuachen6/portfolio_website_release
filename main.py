import logging
import os
import secrets

import flask

import util

# blueprints
from api import api
from article import article
from auth import auth
from editor import editor

app = flask.Flask(__name__)
app.logger.setLevel(logging.INFO)


# session
if not os.path.exists("auth/secrets/secret.txt"):
    with open("auth/secrets/secret.txt", "w") as file:
        file.write(secrets.token_hex())
with open("auth/secrets/secret.txt", "r") as file:
    app.secret_key = file.readline().strip()

# register
app.register_blueprint(api.blueprint)
app.register_blueprint(article.blueprint)
app.register_blueprint(auth.blueprint)
app.register_blueprint(editor.blueprint)


@app.route("/")
def home():
    return flask.redirect("/article/1")


@app.context_processor
def inject_auth():
    return dict(auth=auth.get_auth_level())


@app.before_request
def check_perms():
    path = util.to_path(flask.request.path)
    name, ext = os.path.splitext(os.path.basename(path))
    if ext in [".js", ".mjs", ".css"]:
        return
    if (
        not auth.validate_auth(auth.AuthLevel.PUBLIC)
        and flask.request.endpoint != "auth.login"
    ):
        return flask.redirect(f"/login?redirect={flask.request.full_path}")


if __name__ == "__main__":
    app.run()
