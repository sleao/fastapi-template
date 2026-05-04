from enum import StrEnum


class ItemStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class ItemOrder(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    STATUS = "status"
