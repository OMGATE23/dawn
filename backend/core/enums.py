from enum import StrEnum  # Python 3.11+ (you're on 3.12)

class ToolStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    PROGRESS = "progress"
