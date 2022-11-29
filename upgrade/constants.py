TYPE_MAPPING = {
    "fos": "FosUpdater"
}
PRODUCT_MAPPING = {
    "fortigate": "fgt",
    "fortifirewall": "fwf"
}
TASK_CACHE_KEYS = {
    "status": str,
    "task_id": str,
    "task_data": dict,
    "infosite_builds": set
}
INFOSITE_CACHE_KEYS = {
    "infosite_builds": set
}
STATICS_CACHE_KEYS = {
    "update_get": int,
    "update_post": int,
    "update_delete": int,
    "build_get": int
}
