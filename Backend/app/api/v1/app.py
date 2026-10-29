#!/usr/bin/python3
"""
Flask Application
"""
import os
from os import environ

from flask import Flask, jsonify, make_response
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

if not environ.get('SECRET_KEY') or environ.get('SECRET_KEY') == 'change-me':
    raise RuntimeError(
        "Set a strong SECRET_KEY (python3 -c \"import secrets; "
        "print(secrets.token_hex(32))\")")

from app.models import storage
from app.api.v1.views import app_views

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
app.register_blueprint(app_views)

# Comma separated list of allowed front-end origins, e.g.
# BCV_CORS_ORIGINS=https://certs.example.com
origins = [o.strip() for o in environ.get(
    'BCV_CORS_ORIGINS', 'http://localhost:3000').split(',') if o.strip()]
CORS(app, resources={r"/api/*": {"origins": origins}})


@app.teardown_appcontext
def close_db(error):
    """ Close Storage """
    if error is not None:
        storage.rollback()
    storage.close()


@app.errorhandler(HTTPException)
def http_error(error):
    """ Return every HTTP error as JSON """
    message = error.description if error.description else error.name
    return make_response(jsonify({'error': message}), error.code)


@app.errorhandler(Exception)
def server_error(error):
    app.logger.exception(error)
    return make_response(jsonify({'error': 'Internal server error'}), 500)


if __name__ == "__main__":
    """ Development server (use gunicorn in production) """
    host = environ.get('BCV_API_HOST') or '127.0.0.1'
    port = int(environ.get('BCV_API_PORT') or 5000)
    debug = environ.get("BCV_DEV", "").lower() in ("1", "true", "yes")
    app.run(host=host, port=port, debug=debug, threaded=True)
