#!/usr/bin/python3
"""
Certificate routes that talk to the smart contract
"""
import json
import os
import uuid
from functools import lru_cache

from flask import abort, g, jsonify, request
from web3 import Web3

from app.models import storage
from app.models.certificate import Certificate
from app.models.certificate_request_verification import VerifyCertificate
from app.api.v1.views import app_views
from app.api.v1.views.utilities.encode import generate_keccak256_hash
from app.Authorization.authenticate import require_auth, is_admin, is_self, forbidden

_DEFAULT_ARTIFACT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', '..', '..', 'contracts', 'artifacts', 'contracts',
    'Certificate.sol', 'CertificateVerifier.json')


@lru_cache(maxsize=1)
def get_chain():
    """Connect lazily so the API can start even if the node is down."""
    path = os.environ.get('BCV_CONTRACT_ARTIFACT', _DEFAULT_ARTIFACT)
    try:
        with open(path) as f:
            abi = json.load(f)['abi']
    except FileNotFoundError:
        raise RuntimeError(
            "Contract artifact not found at {}. Run: cd Backend/contracts "
            "&& npm i && npx hardhat compile (or set BCV_CONTRACT_ARTIFACT)"
            .format(os.path.abspath(path)))
    w3 = Web3(Web3.HTTPProvider(
        os.environ.get('BCV_WEB3_PROVIDER', 'http://localhost:8545')))
    address = os.environ.get('BCV_CONTRACT_ADDRESS')
    if not address:
        raise RuntimeError("BCV_CONTRACT_ADDRESS is not set")
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(address), abi=abi)
    return w3, contract


def send_transaction(fn):
    """
    Send a contract transaction. If BCV_PRIVATE_KEY is set the backend wallet
    signs it locally (required for real networks). Otherwise the first
    unlocked node account is used (local Hardhat development only).
    """
    w3, _ = get_chain()
    key = os.environ.get('BCV_PRIVATE_KEY')
    if key:
        account = w3.eth.account.from_key(key)
        tx = fn.build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': w3.eth.chain_id,
        })
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    else:
        tx_hash = fn.transact({'from': w3.eth.accounts[0]})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        raise RuntimeError("Transaction reverted")
    return receipt


def _parse_hash(value):
    value = value[2:] if value.lower().startswith('0x') else value
    raw = bytes.fromhex(value)
    if len(raw) != 32:
        raise ValueError("Certificate hash must be 32 bytes")
    return raw


def _can_issue(certificate):
    return is_admin() or is_self(certificate.school_id)


def _info_to_dict(info):
    return {
        'certificate_hash': info[0].hex(),
        'student_name': info[1],
        'school_name': info[2],
        'school_major': info[3],
        'school_department': info[4],
        'certificate_verify': info[5],
    }


def _set_status(certificate, value):
    status = storage.get_certificates_status(VerifyCertificate, certificate.id)
    if status is None:
        status = VerifyCertificate(
            user_id=certificate.user_id, school_id=certificate.school_id,
            certificate_id=certificate.id)
        storage.add(status)
    status.certificate_status = value


@app_views.route('/add-certificate/<certificate_id>', methods=['POST'])
@require_auth(roles=['school', 'admin'])
def add_contract_certificate(certificate_id):
    """
    Write a certificate to the blockchain (issuing school or admin)
    """
    certificate = storage.get(Certificate, certificate_id)
    if not certificate:
        abort(404, description="Certificate not found")
    if not _can_issue(certificate):
        return forbidden()
    if certificate.certificate_hash:
        abort(409, description="Certificate is already on the blockchain")

    try:
        _, contract = get_chain()
        payload = "{}|{}|{}|{}|{}|{}".format(
            certificate.student_name, certificate.school_name,
            certificate.school_major, certificate.school_department,
            certificate_id, uuid.uuid4())
        certificate_hash = generate_keccak256_hash(payload)
        send_transaction(contract.functions.addCertificate(
            certificate.student_name, certificate.school_name,
            certificate.school_major, certificate.school_department,
            certificate_hash))
        info = contract.functions.getCertificateInfo(certificate_hash).call()
        if not info[1]:
            abort(502, description="Certificate was not stored on-chain")
    except (RuntimeError, ValueError, OSError) as e:
        abort(502, description="Blockchain error: {}".format(e))

    certificate.certificate_hash = info[0].hex()
    _set_status(certificate, "pending")
    storage.save()
    return jsonify({'success': True,
                    'certificate_data': certificate.to_dict()})


@app_views.route('/get-certificate/<string:certificate_hash>',
                 methods=['GET'])
def get_contract_certificate(certificate_hash):
    """
    Public lookup of a certificate on the blockchain (used to verify)
    """
    try:
        _, contract = get_chain()
        info = contract.functions.getCertificateInfo(
            _parse_hash(certificate_hash)).call()
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False,
                        'message': 'Could not query the blockchain'}), 502
    if not info[1]:
        return jsonify({'success': False,
                        'message': 'Certificate not found'}), 404
    return jsonify({'success': True,
                    'certificate_data': _info_to_dict(info)})


@app_views.route('/verify-certificate/<string:certificate_hash>',
                 methods=['PUT'])
@require_auth(roles=['school', 'admin'])
def verify_contract_certificate(certificate_hash):
    """
    Mark a certificate as verified on-chain (issuing school or admin)
    """
    try:
        raw = _parse_hash(certificate_hash)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    certificate = storage.get_certificate_by_hash(raw.hex())
    if not certificate:
        abort(404, description="Certificate not found")
    if not _can_issue(certificate):
        return forbidden()

    try:
        _, contract = get_chain()
        send_transaction(contract.functions.verifyCertificate(raw))
        info = contract.functions.getCertificateInfo(raw).call()
    except Exception as e:
        return jsonify({'success': False,
                        'message': 'Blockchain error: {}'.format(e)}), 400

    certificate.verified_certificate = bool(info[5])
    _set_status(certificate, "verified")
    storage.save()
    response = _info_to_dict(info)
    response['certificate_id'] = certificate.id
    return jsonify({'success': True, 'verified': response})
