"""
Extract certificate fields from an uploaded PDF
"""
import io
import ipaddress
import os
import socket
from urllib.parse import urlparse

import PyPDF2
import requests
from flask import jsonify, request

from app.api.v1.views import app_views
from app.Authorization.authenticate import require_auth

MAX_PDF_BYTES = 10 * 1024 * 1024
# Only download PDFs from these hosts (comma separated env var).
ALLOWED_HOSTS = [h.strip().lower() for h in os.environ.get(
    'BCV_PDF_ALLOWED_HOSTS',
    'firebasestorage.googleapis.com,storage.googleapis.com').split(',')
    if h.strip()]

FIELDS = (
    ('Name:', 'name'),
    ('Email:', 'email'),
    ('School id:', 'school_id'),
    ('School major:', 'school_major'),
    ('School department:', 'school_department'),
    ('School location:', 'school_location'),
    ('School :', 'school'),
    ('School:', 'school'),
)


def _is_safe_url(url):
    """Block SSRF: https only, allow-listed host, public IP addresses only."""
    parsed = urlparse(url or '')
    if parsed.scheme != 'https' or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    if ALLOWED_HOSTS and host not in ALLOWED_HOSTS:
        return False
    try:
        for info in socket.getaddrinfo(host, parsed.port or 443):
            ip = ipaddress.ip_address(info[4][0])
            if (ip.is_private or ip.is_loopback or ip.is_link_local
                    or ip.is_reserved or ip.is_multicast):
                return False
    except (socket.gaierror, ValueError):
        return False
    return True


@app_views.route('/pdf-data', methods=['POST'], strict_slashes=False)
@require_auth
def pdf_data():
    """
    Retrieve the certificate fields from a PDF document.
    """
    body = request.get_json(silent=True) or {}
    pdf_url = body.get("pdfURL")
    if not _is_safe_url(pdf_url):
        return jsonify({'error': 'pdfURL is missing or not allowed'}), 400

    try:
        response = requests.get(pdf_url, timeout=15, stream=True,
                                allow_redirects=False)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to download the PDF'}), 400
        content = response.raw.read(MAX_PDF_BYTES + 1, decode_content=True)
        if len(content) > MAX_PDF_BYTES:
            return jsonify({'error': 'PDF is too large'}), 413
    except requests.RequestException:
        return jsonify({'error': 'Failed to download the PDF'}), 400

    try:
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = reader.pages[0].extract_text() or ''
    except Exception:
        return jsonify({'error': 'Could not read the PDF'}), 400

    data = {}
    for line in text.split('\n'):
        line = line.strip()
        for prefix, key in FIELDS:
            if line.startswith(prefix):
                data[key] = line[len(prefix):].strip()
                break
    return jsonify(data)
