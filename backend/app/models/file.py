from enum import StrEnum


class FileRole(StrEnum):
    SOURCE = "source"


class PipelineStatus(StrEnum):
    PENDING = "pending"
    NOT_STARTED = "not_started"
