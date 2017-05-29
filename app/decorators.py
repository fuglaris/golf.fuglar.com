from functools import wraps
from flask import request, abort, redirect, url_for

from app.models import (SessionContext, User)
from app.constants import ROLE

from flask_login import (
    login_user,
    logout_user,
    current_user,
    login_required
)

def my_logger(orig_func):
    import logging
    logger = logging.getLogger('function_logger')
    hdlr = logging.FileHandler('function.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.WARNING)

    @wraps(orig_func)
    def wrapper(*args, **kwargs):
        logger.info(
            'Ran with args: {}, and kwargs: {}'.format(args, kwargs))
        return orig_func(*args, **kwargs)
    return wrapper


def requires_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            with SessionContext() as session:
                role = session.query(User).filter_by(id=current_user.id).first()
                userrole = ROLE[int(role.role)]
                if userrole not in roles:
                    return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return wrapped
    return wrapper


def validate_json(*expected_args):
    def decorator(orig_func):
        @wraps(orig_func)
        def wrapper(*args, **kwargs):
            json_object = request.get_json()
            for expected_arg in expected_args:
                if expected_arg not in json_object:
                    abort(400)
            return orig_func(*args, **kwargs)
        return wrapper
    return decorator

def validate_login(orig_func):
    @wraps(orig_func)
    def wrapper(*args, **kwargs):
        for form_object in request.form:
            if form_object not in ['password','email','remember_me']:
                abort(400)
        return orig_func(*args, **kwargs)
    return wrapper

def validate_registration(orig_func):
    @wraps(orig_func)
    def wrapper(*args, **kwargs):
        for form_object in request.form:
            if form_object not in ['password','name','email','company']:
                abort(400)
        return orig_func(*args, **kwargs)
    return wrapper

def validate_provider(orig_func):
    @wraps(orig_func)
    def wrapper(*args, **kwargs):
        if kwargs['provider'] in ['facebook','google','microsoft']:
            return orig_func(*args, **kwargs)
        abort(400)
    return wrapper

def is_logged_in(orig_func):
    @wraps(orig_func)
    def wrapper(*args, **kwargs):
        try:
            if not current_user.is_anonymous():
                return redirect(url_for('main.index'))
        except TypeError:
            return orig_func(*args, **kwargs)
    return wrapper
