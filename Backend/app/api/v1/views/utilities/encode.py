#!/usr/bin/python3
"""
Generate keccak256 hash
"""
from web3 import Web3


def generate_keccak256_hash(string):
    """Return the 32-byte Keccak-256 (Ethereum) hash of a string."""
    return bytes(Web3.keccak(text=string))
