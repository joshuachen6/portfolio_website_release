import enum
import os
import time
import uuid
import qrcode

import flask
from functools import wraps

import pyotp
import yaml

import util
from util import DataBase

blueprint = flask.Blueprint('auth', __name__, template_folder='templates')
auth_root = os.path.join('auth', 'secrets')
os.makedirs(auth_root, exist_ok=True)

totp_path = os.path.join(auth_root, 'totp.txt')
if not os.path.exists(totp_path):
    with open(totp_path, 'w') as file:
        file.write(pyotp.random_base32())


with open(totp_path, 'r') as file:
    totp = pyotp.totp.TOTP(file.readline().strip())
    code_path = os.path.join(auth_root, 'code.png')
    if not os.path.exists(code_path):
        url = totp.provisioning_uri(name='jc@portfolio', issuer_name='server')
        image = qrcode.make(url)
        image.save(code_path)


class TokenManager:

    @staticmethod
    def create_token(level):
        database = DataBase()

        database.cursor.execute(
            """
            DELETE FROM sessions
            WHERE ? - timestamp > ?;
            """,
            (int(time.time()), util.get_config('token_expiration'))
        )

        token = str(uuid.uuid4())

        database.cursor.execute(
            """
            INSERT INTO sessions(token, timestamp, level)
            VALUES(?, ?, ?);
            """,
            (token, int(time.time()), level.value)
        )

        database.connection.commit()

        return token

    @staticmethod
    def validate_token(token):
        database = DataBase()

        database.cursor.execute(
            """
            SELECT timestamp, level FROM sessions
            WHERE token = ?;
            """,
            (token,)
        )
        result = database.cursor.fetchone()

        if result is not None:
            timestamp, level = result
            if time.time() - timestamp < util.get_config('token_expiration'):
                return level
        return None

    @staticmethod
    def revoke_token(token):
        database = DataBase()

        database.cursor.execute(
            """
            DELETE FROM sessions
            WHERE token = ?;
            """,
            (token,)
        )

        database.connection.commit()

    @staticmethod
    def renew_token(token):
        database = DataBase()

        database.cursor.execute(
            """
            UPDATE sessions
            SET timestamp = ?
            WHERE token = ?;
            """,
            (int(time.time()), token)
        )

        database.connection.commit()


class AuthLevel(enum.Enum):
    PUBLIC = 1
    PRIVATE = 2


def validate_auth(level=AuthLevel.PRIVATE):
    return get_auth_level() >= level.value


def get_auth_level():
    if 'token' in flask.session:
        token = flask.session['token']
        level = TokenManager.validate_token(token)
        TokenManager.renew_token(token)
        if level is not None:
            return level
    return 0


def can_view(visibility):
    if visibility == 0:
        if not validate_auth(AuthLevel.PRIVATE):
            return False
    return True


def require_auth(route):

    @wraps(route)
    def auth():
        if validate_auth():
            return route()
        return flask.redirect(f'/login?redirect={flask.request.full_path}')

    return auth


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return flask.render_template('login.html')
    elif flask.request.method == 'POST':
        credentials = flask.request.form
        with open(os.path.join(auth_root, 'password.yaml'), 'r') as file:
            passwords = yaml.safe_load(file)
            if passwords['private'] == credentials['password'] and credentials['token'] == totp.now():
                auth_level = AuthLevel.PRIVATE
            elif passwords['public'] == credentials['password']:
                auth_level = AuthLevel.PUBLIC
            else:
                return flask.make_response('', 401)

            flask.session['token'] = TokenManager.create_token(auth_level)
            return flask.make_response('', 200)


@blueprint.route('/logout')
def logout():
    if 'token' in flask.session:
        TokenManager.revoke_token(flask.session.pop('token'))
    return flask.redirect('/')


def visibility():
    return 0 if validate_auth() else 1
