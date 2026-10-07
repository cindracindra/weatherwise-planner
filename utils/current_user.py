"""Whose calendar a request is for: the signed-in account.

Routes only run for signed-in users (see utils.auth.require_login), so
current_user here is always a real AppUser loaded from the session.
"""

from flask_login import current_user


def current_user_id() -> int:
    """The id of the signed-in account."""
    return current_user.id
