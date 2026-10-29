#!/usr/bin/python3
"""
School API actions
"""
from app.models import storage
from app.api.v1.views import app_views
from app.models.school import School
from app.Authorization.authenticate import (
    require_auth, is_admin, is_self, forbidden)
from flask import abort, jsonify, make_response, request

SCHOOL_EDITABLE = {'school_name', 'school_location', 'password',
                   'profile_url', 'about_profile', 'phone_number'}
ADMIN_EDITABLE = SCHOOL_EDITABLE | {'email'}


@app_views.route('/schools', methods=['GET'], strict_slashes=False)
@require_auth
def get_schools():
    """Retrieves the list of all schools (any signed-in account)"""
    return jsonify([s.to_dict() for s in storage.all(School).values()])


@app_views.route('/schools/<school_id>', methods=['GET'], strict_slashes=False)
@require_auth
def get_school(school_id):
    """Retrieves a school"""
    school = storage.get(School, school_id)
    if not school:
        abort(404)
    return jsonify(school.to_dict())


@app_views.route('/schools/<school_id>', methods=['DELETE'],
                 strict_slashes=False)
@require_auth
def delete_school(school_id):
    """Deletes a school (the school itself or an admin)"""
    if not (is_self(school_id) or is_admin()):
        return forbidden()
    school = storage.get(School, school_id)
    if not school:
        abort(404)
    storage.delete(school)
    storage.save()
    return make_response(jsonify({}), 200)


@app_views.route('/schools', methods=['POST'], strict_slashes=False)
def post_school():
    """Creates a school (public sign-up). The role is always 'school'."""
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
              if k in SCHOOL_EDITABLE | {'email'}}
    instance = School(**fields)
    instance.save()
    return make_response(jsonify(instance.to_dict()), 201)


@app_views.route('/schools/<school_id>', methods=['PUT'], strict_slashes=False)
@require_auth
def put_school(school_id):
    """Updates a school (the school itself or an admin)"""
    if not (is_self(school_id) or is_admin()):
        return forbidden()
    school = storage.get(School, school_id)
    if not school:
        abort(404)
    data = request.get_json(silent=True)
    if not data:
        abort(400, description="Not a JSON")

    allowed = ADMIN_EDITABLE if is_admin() else SCHOOL_EDITABLE
    for key, value in data.items():
        if key in allowed:
            if key == 'password' and not value:
                continue
            setattr(school, key, value)
    storage.save()
    return make_response(jsonify(school.to_dict()), 200)
