#!/usr/bin/python3
"""
Certificate verify request API action
"""
from app.models import storage
from app.api.v1.views import app_views
from app.models.certificate import Certificate
from app.models.certificate_request_verification import VerifyCertificate
from app.Authorization.authenticate import require_auth, is_admin, is_self, forbidden
from flask import abort, jsonify, make_response


@app_views.route('/certificate/<certificate_id>/request/verify',
                 methods=['POST'], strict_slashes=False)
@require_auth
def request_user_certificate_verification(certificate_id):
    """
    The owner of a certificate asks the school to verify it
    (marks the certificate as 'pending').
    """
    certificate = storage.get(Certificate, certificate_id)
    if not certificate:
        abort(404, description="Certificate not found")
    if not (is_admin() or is_self(certificate.user_id)):
        return forbidden()

    status = storage.get_certificates_status(VerifyCertificate, certificate_id)
    if status is None:
        status = VerifyCertificate(
            user_id=certificate.user_id, school_id=certificate.school_id,
            certificate_id=certificate_id)
    if status.certificate_status == "verified":
        abort(409, description="Certificate is already verified")
    status.certificate_status = "pending"
    status.save()
    return make_response(jsonify(status.to_dict()), 201)
