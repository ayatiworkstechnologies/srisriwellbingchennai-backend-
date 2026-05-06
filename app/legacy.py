ACTIVE_FLAG_TRUE = "true"
ACTIVE_FLAG_FALSE = "false"


def to_active_flag(value: bool) -> str:
    return ACTIVE_FLAG_TRUE if value else ACTIVE_FLAG_FALSE


def is_active_flag(value: str | None) -> bool:
    return value == ACTIVE_FLAG_TRUE
