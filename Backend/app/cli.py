"""
Admin management.  Usage (from Backend/):

    python -m app.cli create-admin you@example.com "Your Name"

The password is read from the prompt (or BCV_ADMIN_PASSWORD).
"""
import getpass
import os
import sys

from app.models import storage
from app.models.admin import Admin


def create_admin(email, username):
    if storage.email_in_use(email):
        sys.exit("That email is already registered.")
    password = os.environ.get('BCV_ADMIN_PASSWORD') or getpass.getpass(
        "Password (min 10 chars): ")
    if len(password) < 10:
        sys.exit("Password too short.")
    Admin(email=email, username=username, password=password,
          is_superadmin=True).save()
    print("Super admin created:", email)


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "create-admin":
        sys.exit(__doc__)
    create_admin(sys.argv[2], sys.argv[3] if len(sys.argv) > 3
                 else sys.argv[2].split("@")[0])
