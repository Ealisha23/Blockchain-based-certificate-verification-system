#!/usr/bin/python3
"""
User API actions
"""
from app.models import storage
from app.api.v1.views import app_views
from app.models.user import User
from app.Authorization.authenticate import (
    require_auth, is_admin, is_self, forbidden)
from flask import abort, jsonify, make_response, request

# Fields a normal user may change on their own profile
USER_EDITABLE = {'first_name', 'last_name', 'password', 'profile_url',
                 'phone_number', 'about_profile'}
# Fields only an admin may additionally change
ADMIN_EDITABLE = USER_EDITABLE | {'email', 'role'}


@app_views.route('/users', methods=['GET'], strict_slashes=False)
@require_auth(roles=['admin', 'school'])
def get_users():
    """Retrieves the list of all users (admins and schools only)"""
    return jsonify([u.to_dict() for u in storage.all(User).values()])


@app_views.route('/users/<user_id>', methods=['GET'], strict_slashes=False)
@require_auth
def get_user(user_id):
    """Retrieves a user (the user themself, a school or an admin)"""
    from flask import g
    if not (is_self(user_id) or is_admin()
            or g.identity.get('role') == 'school'):
        return forbidden()
    user = storage.get(User, user_id)
    if not user:
        abort(404)
    return jsonify(user.to_dict())


@app_views.route('/users/<user_id>', methods=['DELETE'],
                 strict_slashes=False)
@require_auth
def delete_user(user_id):
    """Deletes a user (the user themself or an admin)"""
    if not (is_self(user_id) or is_admin()):
        return forbidden()
    user = storage.get(User, user_id)
    if not user:
        abort(404)
    storage.delete(user)
    storage.save()
    return make_response(jsonify({}), 200)


@app_views.route('/users', methods=['POST'], strict_slashes=False)
def post_user():
    """Creates a user (public sign-up). The role is always 'user'."""
    data = request.get_json(silent=True)
    if not data:
        abort(400, description="Not a JSON")
    if not data.get('email'):
        abort(400, description="Missing email")
    if not data.get('password'):
        abort(400, description="Missing password")
    if storage.email_in_use(data['email']):
        abort(409, description="Email already registered")

    fields = {k: v for k, v in data.items()
              if k in USER_EDITABLE | {'email'}}
    instance = User(**fields)
    instance.save()
    return make_response(jsonify(instance.to_dict()), 201)


@app_views.route('/users/<user_id>', methods=['PUT'], strict_slashes=False)
@require_auth
def put_user(user_id):
    """Updates a user (the user themself or an admin)"""
    if not (is_self(user_id) or is_admin()):
        return forbidden()
    user = storage.get(User, user_id)
    if not user:
        abort(404)
    data = request.get_json(silent=True)
    if not data:
        abort(400, description="Not a JSON")

    allowed = ADMIN_EDITABLE if is_admin() else USER_EDITABLE
    for key, value in data.items():
        if key in allowed:
            if key == 'password' and not value:
                continue
            setattr(user, key, value)
    storage.save()
    return make_response(jsonify(user.to_dict()), 200)
