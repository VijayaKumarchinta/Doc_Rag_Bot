from uuid import UUID


def is_valid_session_id(raw):
    if not raw:
        return False
    try:
        UUID(str(raw))
        return True
    except (TypeError, ValueError):
        return False


def history(session_id):
    return []


def append_turn(session_id, question, answer):
    return None
