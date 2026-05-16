from settings import settings

_refine_count = 0


def check_and_increment() -> bool:
    global _refine_count
    if _refine_count >= settings.claude_daily_limit:
        return False
    _refine_count += 1
    return True


def remaining() -> int:
    return max(0, settings.claude_daily_limit - _refine_count)
