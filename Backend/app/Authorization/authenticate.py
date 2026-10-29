"""
JWT authentication / authorization helpers.
"""
import os
from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import g, jsonify, request

ALGORITHM = "HS256"
TOKEN_LIFETIME = timedelta(days=1)


def get_secret():
    secret = os.environ.get("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY environment variable is not set")
    return secret


def create_token(payload):
    """Encode a signed token that expires after TOKEN_LIFETIME."""
    claims = dict(payload)
    claims["exp"] = int((datetime.utcnow() + TOKEN_LIFETIME).timestamp())
    return jwt.encode(claims, get_secret(), algorithm=ALGORITHM)


def _decode_request_token():
    header = request.headers.get("Authorization", "")
    parts = header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None, (jsonify({"message": "Authorization required"}), 401)
    try:
        return jwt.decode(parts[1], get_secret(), algorithms=[ALGORITHM]), None
    except jwt.ExpiredSignatureError:
        return None, (jsonify({"message": "Token expired"}), 401)
    except jwt.InvalidTokenError:
        return None, (jsonify({"message": "Invalid token"}), 401)


def require_auth(func=None, roles=None):
    """
    Require a valid JWT. Usable as ``@require_auth`` or
    ``@require_auth(roles=["admin"])``. The decoded claims are available as
    ``flask.g.identity``.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            claims, error = _decode_request_token()
            if error:
                return error
            if roles and claims.get("role") not in roles:
                return jsonify({"message": "Forbidden"}), 403
            g.identity = claims
            return f(*args, **kwargs)
        return wrapper
    if func is not None and callable(func):
        return decorator(func)
    return decorator


def is_admin():
    return getattr(g, "identity", {}).get("role") == "admin"


def is_superadmin():
    ident = getattr(g, "identity", {})
    return ident.get("role") == "admin" and bool(ident.get("is_superadmin"))


def is_self(object_id):
    return getattr(g, "identity", {}).get("user_id") == object_id


def forbidden():
    return jsonify({"message": "Forbidden"}), 403
