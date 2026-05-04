from enum import StrEnum


class UserRoles(StrEnum):
    ADMINISTRATOR = "ADMINISTRATOR"
    RESPONSIBLE = "RESPONSIBLE"
    READER = "READER"
    MANAGER = "MANAGER"
