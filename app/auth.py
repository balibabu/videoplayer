from functools import wraps

from flask import Response, current_app, request


def check_auth(username, password):
    return (
        username == current_app.config["AUTH_USERNAME"]
        and password == current_app.config["AUTH_PASSWORD"]
    )


def authenticate():
    return Response(
        "Access denied. Please provide valid credentials.",
        401,
        {"WWW-Authenticate": f'Basic realm="{current_app.config["AUTH_REALM"]}"'},
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated
