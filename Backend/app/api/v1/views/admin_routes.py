#!/usr/bin/python3
"""
Admin user routes
"""
from flask import jsonify, request, make_response, abort
from app.models.admin import Admin
from app.models import storage
from app.api.v1.views import app_views
from app.Authorization.authenticate import (
    create_token, require_auth, is_superadmin, forbidden)

ADMIN_EDITABLE = {'username', 'password', 'email'}


@app_views.route('/login-admin', methods=['POST'])
def admin_login():
    data = request.get_json(silent=True) or {}
    user_mail = data.get('userMail')
    password = data.get('password')
    if not password:
        return jsonify({'message': 'Password field is required'}), 400
    if not user_mail:
        return jsonify({'message': 'Email field is required'}), 400

    admin = storage.get_email(Admin, user_mail)
    if not admin or not admin.check_password(password):
        return jsonify({'message': 'Invalid email or password'}), 401

    return jsonify({'token': create_token({
        'user_name': admin.username,
        'user_email': admin.email,
        'user_id': admin.id,
        'is_superadmin': bool(admin.is_superadmin),
        'role': admin.role,
    })})


@app_views.route('/admins', methods=['GET'], strict_slashes=False)
@require_auth(roles=['admin'])
def get_admins():
    """Retrieves the list of all admins"""
    return jsonify([a.to_dict() for a in storage.all(Admin).values()])


@app_views.route('/admins/<admin_id>', methods=['GET'], strict_slashes=False)
@require_auth(roles=['admin'])
def get_admin(admin_id):
    """Retrieves an admin"""
    admin = storage.get(Admin, admin_id)
    if not admin:
        abort(404)
    return jsonify(admin.to_dict())


@app_views.route('/admins/<admin_id>', methods=['DELETE'],
                 strict_slashes=False)
@require_auth(roles=['admin'])
def delete_admin(admin_id):
    """Deletes an admin (super admins only)"""
    if not is_superadmin():
        return forbidden()
    admin = storage.get(Admin, admin_id)
    if not admin:
        abort(404)
    storage.delete(admin)
    storage.save()
    return make_response(jsonify({}), 200)


@app_views.route('/admins', methods=['POST'], strict_slashes=False)
@require_auth(roles=['admin'])
def post_admin():
    """Creates an admin (super admins only)"""
    if not is_superadmin():
        return forbidden()
    data = request.get_json(silent=True)
    if not data:
        abort(400, description="Not a JSON")
    if not data.get('email'):
        abort(400, description="Missing email")
    if not data.get('password'):
        abort(400, description="Missing password")
    if storage.email_in_use(data['email']):
        abort(409, description="Email already registered")

    fields = {k: v for k, v in data.items() if k in ADMIN_EDITABLE}
    fields.setdefault('username', data['email'].split('@')[0])
    instance = Admin(**fields)
    instance.save()
    return make_response(jsonify(instance.to_dict()), 201)


@app_views.route('/admins/<admin_id>', methods=['PUT'], strict_slashes=False)
@require_auth(roles=['admin'])
def put_admin(admin_id):
    """Updates an admin (super admins, or the admin themself)"""
    from app.Authorization.authenticate import is_self
    if not (is_superadmin() or is_self(admin_id)):
        return forbidden()
    admin = storage.get(Admin, admin_id)
    if not admin:
        abort(404)
    data = request.get_json(silent=True)
    if not data:
        abort(400, description="Not a JSON")
    for key, value in data.items():
        if key in ADMIN_EDITABLE:
            if key == 'password' and not value:
                continue
            setattr(admin, key, value)
    storage.save()
    return make_response(jsonify(admin.to_dict()), 200)
