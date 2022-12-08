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
    "update_get": int,
    "update_post": int,
    "update_delete": int,
    "build_get": int
}
IMAGE_CACHE_KEYS = {
    "file": str,
    "pkg": dict
}
