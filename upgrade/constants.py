from enum import Enum


TYPE_MAPPING = {
    "fos": "FosUpdater"
}
PRODUCT_MAPPING = {
    "fortigate": "fgt",
    "fortiwifi": "fwf"
}
TASK_CACHE_KEYS = {
    "status": str,
    "task_id": str,
    "task_lock": str,
    "task_data": dict,
    "task_type": str
}
INFOSITE_CACHE_KEYS = {
    "builds": set,
    "releases": list
}
STATICS_CACHE_KEYS = {
    "total_upgrades": int,
    "total_build_query": int
}
IMAGE_CACHE_KEYS = {
    "file": str,
    "pkg": dict
}


class TaskStatusCode(Enum):
    COMPLETED = "completed"
    PENDING = "pending"
    IN_PROGRESS = "in progress"
    FAILED = "failed"
    CANCELLED = "cancelled"
    OK = "ok"
    ERROR = "error"
