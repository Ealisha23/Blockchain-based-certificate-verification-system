#!/usr/bin/python3
"""
Index api route
"""
from flask import jsonify
from app.models.user import User
from app.models.school import School
from app.models.certificate import Certificate
from app.models import storage
from app.api.v1.views import app_views
from app.Authorization.authenticate import require_auth


@app_views.route('/status', methods=['GET'], strict_slashes=False)
def status():
    """
    Status of API
    """
    return jsonify({"status": "OK"})


@app_views.route('/stats', methods=['GET'], strict_slashes=False)
@require_auth(roles=['admin'])
def number_objects():
    """
    Retrieves the number of each objects by type (admins only)
    """
    classes = [User, School, Certificate]
    names = ["users", "schools", "certificate"]

    num_objs = {}
    for cls, name in zip(classes, names):
        num_objs[name] = storage.count(cls)
        num_objs[name + "_increase"] = storage.increase(cls)

    num_objs["verified_certificate"] = storage.verified_certificate_count()

    return jsonify(num_objs)
