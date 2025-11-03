from enum import Enum


class DatabaseType(Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class ValidationStatus(Enum):
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    UNSAFE = "unsafe"

