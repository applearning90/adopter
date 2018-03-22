from flask import redirect, render_template, request, session
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'profile' not in session:
            return redirect("/home")
        return f(*args, **kwargs)
    return decorated_function

def checkbox(value):
    if value == 1:
        return True
    else:
        return False
