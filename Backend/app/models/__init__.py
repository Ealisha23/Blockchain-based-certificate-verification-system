#!/usr/bin/python3
"""
initialize the models package
"""

from os import getenv


storage_t = getenv("BCV_TYPE_STORAGE")

if storage_t == "db":
    from app.models.engine.db_storage import DBstorage
    storage = DBstorage()
else:
    raise RuntimeError(
        "BCV_TYPE_STORAGE must be set to 'db' (got {!r}). "
        "Only SQL-backed storage is implemented; certificate hashes are "
        "written to the blockchain through the contract routes.".format(storage_t))
storage.reload()
