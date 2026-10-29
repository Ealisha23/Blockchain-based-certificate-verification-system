"""
Helper to decode raw contract event logs (debugging utility)
"""
import json
import os

import eth_abi
from eth_utils import decode_hex

_DEFAULT_ARTIFACT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', '..', '..', '..', 'contracts', 'artifacts', 'contracts',
    'Certificate.sol', 'CertificateVerifier.json')


def format_raw_data(logs, event_name):
    """Decode the non-indexed data of each log of `event_name`."""
    path = os.environ.get('BCV_CONTRACT_ARTIFACT', _DEFAULT_ARTIFACT)
    with open(path) as f:
        abi = json.load(f)['abi']
    types, names = [], []
    for elem in abi:
        if elem.get('type') == 'event' and elem.get('name') == event_name:
            for item in elem['inputs']:
                if not item['indexed']:
                    types.append(item['type'])
                    names.append(item['name'])
            break
    decoded = []
    for log in logs:
        values = eth_abi.decode(types, decode_hex(log['data']))
        decoded.append(dict(zip(names, values)))
    return decoded
