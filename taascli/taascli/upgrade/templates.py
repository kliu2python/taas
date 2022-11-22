CONFIG_TEMPLATES_JSON = """[{
    "platform": "fos",
    "build_info": {
        "version": "v7.00",
        "repo": "FortiOS",
        "branch": "",
        "build": 0,
        "type": "image"
    },
    "device_access": {
        "host": "xxx.xxx.xxx.xxx",
        "username": "admin",
        "password": "admin"
    }
},
{
    "platform": "fos",
    "build_info": {
        "version": "v7.00",
        "repo": "AVEngine",
        "branch": "",
        "build": 0,
        "type": "av",
        "file_pattern": "avengine-v7.(.*)-fosv(.*).tgz"
    },
    "device_access": {
        "host": "xxx.xxx.xxx.xxx",
        "username": "admin",
        "password": "admin"
    }
}]"""

CONFIG_TEMPLATES_YAML = """---
platform: fos
build_info: 
    version: v7.00
    # product: fgt  This is not required for FortiGate and FortiFirewall
    repo: FortiOS
    branch: ""
    build: 0
    type: image
device_access: 
    host: xxx.xxx.xxx.xxx
    username: username
    password: password
---
platform: fos
build_info: 
    version: v7.00
    # product: fgt  This is not required for FortiGate and FortiFirewall
    repo: AVEngine
    branch: ""
    build: 0
    type: av
    file_pattern: avengine-v7.(.*)-fosv(.*).tgz
device_access: 
    host: xxx.xxx.xxx.xxx
    username: username
    password: password
"""