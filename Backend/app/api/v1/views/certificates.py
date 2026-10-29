#!/usr/bin/python3
"""
Certificate API actions
"""
from datetime import datetime
from app.models import storage
from app.api.v1.views import app_views
from app.models.certificate import Certificate
from app.models.certificate_request_verification import VerifyCertificate
from app.models.school import School
from app.models.user import User
from app.Authorization.authenticate import (
    require_auth, is_admin, is_self, forbidden)
from flask import abort, g, jsonify, make_response, request

CREATE_FIELDS = ('student_name', 'student_email', 'school_id', 'school_name',
                 'school_major', 'school_department', 'school_location')
UPDATABLE = {'student_name', 'student_email', 'school_name', 'school_major',
             'school_department', 'school_location', 'completion_data'}


def can_access(certificate):
    """Admin, the owning student or the issuing school"""
    return (is_admin() or is_self(certificate.user_id)
            or is_self(certificate.school_id))


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00')
                                      ).replace(tzinfo=None)
    except ValueError:
        abort(400, description="Invalid completion_data (use ISO date)")


def certificate_with_status(certificate):
    data = certificate.to_dict()
    status = storage.get_certificates_status(VerifyCertificate, certificate.id)
    data["certificate_status"] = (
        status.certificate_status if status else "unverified")
    return data


@app_views.route('/certificate', methods=['GET'], strict_slashes=False)
@require_auth(roles=['admin'])
def get_certificate():
    """Retrieves all certificates (admins only)"""
    return jsonify([c.to_dict() for c in storage.all(Certificate).values()])


@app_views.route('/users/<user_id>/certificate', methods=['GET'],
                 strict_slashes=False)
@require_auth
def get_user_certificate(user_id):
    """Retrieves the certificates of a user (or issued by a school)"""
    if not (is_self(user_id) or is_admin()):
        return forbidden()
    certificates = storage.get_user_certificates(Certificate, user_id)
    if not certificates:
        abort(404, description="No certificate was found")
    return jsonify([certificate_with_status(c) for c in certificates])


@app_views.route('/certificate/<certificate_id>',
                 methods=['GET'], strict_slashes=False)
@require_auth
def get_Certificate(certificate_id):
    """Retrieves a certificate"""
    certificate = storage.get(Certificate, certificate_id)
    if not certificate:
        abort(404)
    if not can_access(certificate):
        return forbidden()
    return jsonify(certificate_with_status(certificate))


@app_views.route('/users/<user_id>/certificates/<certificate_id>',
                 methods=['DELETE'], strict_slashes=False)
@require_auth
def delete_Certificate(user_id, certificate_id):
    """Deletes a certificate"""
    certificate = storage.get(Certificate, certificate_id)
    if not certificate:
        abort(404)
    if not can_access(certificate):
        return forbidden()
    storage.delete(certificate)
    storage.save()
    return make_response(jsonify({}), 200)


@app_views.route('/users/<user_id>/certificates', methods=['POST'],
                 strict_slashes=False)
@require_auth
def post_certificate(user_id):
    """
    Creates a certificate for a student. Allowed for the student themself,
    for the issuing school, or for an admin.
    """
    data = request.get_json(silent=True)
    if not data:
        abort(400, description="Not a JSON")
    for field in CREATE_FIELDS:
        if not data.get(field):
            abort(400, description="Missing {}".format(field))

    if not (is_admin() or is_self(user_id) or is_self(data['school_id'])):
        return forbidden()
    if not storage.get(User, user_id):
        abort(404, description="Student not found")
    if not storage.get(School, data['school_id']):
        abort(404, description="School not found")

    fields = {k: data[k] for k in CREATE_FIELDS}
    fields['completion_data'] = _parse_date(data.get('completion_data'))
    fields['user_id'] = user_id
    instance = Certificate(**fields)
    status = VerifyCertificate(user_id=user_id, school_id=instance.school_id,
                               certificate_id=instance.id,
                               certificate_status="unverified")
    storage.add(instance)
    storage.save()  # certificate first: the status row has a foreign key
    status.save()
    certificate = instance.to_dict()
    certificate["certificate_status"] = status.certificate_status
    return make_response(jsonify(certificate), 201)


@app_views.route('/users/<user_id>/certificates/<certificate_id>',
                 methods=['PUT'], strict_slashes=False)
@require_auth
def put_certificate(user_id, certificate_id):
    """Updates a certificate (never its hash / verified flag)"""
    certificate = storage.get(Certificate, certificate_id)
    if not certificate:
        abort(404)
    if not can_access(certificate):
        return forbidden()
    if certificate.certificate_hash:
        abort(409, description="Certificate is already on the blockchain")
    data = request.get_json(silent=True)
    if not data:
        abort(400, description="Not a JSON")
    for key, value in data.items():
        if key in UPDATABLE:
            if key == 'completion_data':
                value = _parse_date(value)
            setattr(certificate, key, value)
    storage.save()
    return make_response(jsonify(certificate.to_dict()), 200)
