from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    admin = "admin"
    supervisor = "supervisor"
    operator = "operator"
    maintenance = "maintenance"


ROLE_ORDER: dict[Role, int] = {
    Role.operator: 10,
    Role.maintenance: 20,
    Role.supervisor: 30,
    Role.admin: 40,
}


def role_at_least(user_role: Role, required: Role) -> bool:
    return ROLE_ORDER[user_role] >= ROLE_ORDER[required]

