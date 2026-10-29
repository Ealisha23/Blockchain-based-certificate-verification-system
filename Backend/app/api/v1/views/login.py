#!/usr/bin/python3
"""
User / school login module
"""
from flask import jsonify, request
from app.models.user import User
from app.models.school import School
from app.models import storage
from app.api.v1.views import app_views
from app.Authorization.authenticate import create_token


@app_views.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    user_mail = data.get('userMail')
    password = data.get('password')
    if not password:
        return jsonify({'message': 'Password field is required'}), 400
    if not user_mail:
        return jsonify({'message': 'Email field is required'}), 400

    user = storage.get_email(User, user_mail)
    if user and user.check_password(password):
        return jsonify({'token': create_token({
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_email': user.email,
            'user_id': user.id,
            'role': user.role,
        })})

    school = storage.get_email(School, user_mail)
    if school and school.check_password(password):
        return jsonify({'token': create_token({
            'first_name': school.school_name,
            'user_email': school.email,
            'user_id': school.id,
            'role': school.role,
        })})

    # Same message whether the email or the password was wrong
    return jsonify({'message': 'Invalid email or password'}), 401
