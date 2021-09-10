DATASTORE_POOL_KEYS = {
    "active_pool": set,
    "pool_id": str,
    "pool_type": str,
    "pool_data": dict,
    "pool_status": str,
    "pool_create_time": str,
    "pool_expiration": float,
    "pool_life": int,
    "pool_res_life": int,
    "pool_capacity": int,
    "pool_res_avaliable": set,
    "pool_res_assigned": set,
    "pool_res_share": int
}

DATASTORE_RESOURCE_KEYS = {
    "res_id": str,
    "res_time": str,
    "res_expire": float,
    "res_data": dict
}

DATASTORE_WORKER_KEYS = {
    "worker_data": set
}

POOL_TYPE = {
    "fortigate.user"
}

TYPE_MAPPING = {
    "fortigate.user": "User"
}

FTM_IOS = {
    'd': {
        'registration_id': ('966a674eda38db20c325a9dfd6a1242935114b9'
                            '4796423d34aa4170c8cf97819'),
        '__device_version': '4.9.9_IOS',
        'mobile_id': '00DAB39B-B920-463A-A099-44B6138A3C95',
        'token_activation_code': 'AAAAAAAAAAAAAAAAA',
        '__type': 'SoftToken.MobileProvisionRequest',
        '__version': '5',
        '__device_build': '4.9.9.0009'
    }
}
FTM_ANDRIOD = {
    'd': {
        'registration_id': ('dzbg2OOiDYM:APA91bF7EP6PJ9J9F2aIiFEbt24I4GPWhMcQz'
                            'ul_bsW8aJtBbxg5m9aubv1F9E63nil2DQHxCb5GU8upUHk6Eo'
                            '_yvASBxg7C2a6UoHhQTMXAHm6lPLeJq9oE7jQVCvVVJczsISV'
                            'U-xDJ'),
        '__device_version': '4.9.9_Android',
        'mobile_id': '00DAB39B-B920-463A-A099-44B6138A3C95',
        'token_activation_code': 'AAAAAAAAAAAAAAAAA',
        '__type': 'SoftToken.MobileProvisionRequest',
        '__version': '5',
        '__device_build': '4.9.9.0009'
    }
}
