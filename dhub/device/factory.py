def get_device(config, device_slot_id):
    os_version = config.get("os")
    if "android" in [os_version]:
        android_device_cls = __import__(
            "mobile_device_hub.device.android.android_device", fromlist=[""]
        ).__getattribute__("AndroidDevice")
        return android_device_cls(config, device_slot_id)
