CONFIG_TEMPLATES_JSON = """[{
    "platform": "fos",
    "build_info": {
        "repo": "FortiOS",
        "branch": "",
        "release": "7.0.1"
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
        "repo": "AVEngine",
        "branch": "",
        "release": "7"
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
    # product: fgt  This is not required for FortiGate and FortiFirewall
    repo: FortiOS
    branch: ""
    release: 7.0.1      # 7.0.1ga OR  7 for latest of the trunk if build = 0
    build: 0
    type: image
device_access: 
    host: xxx.xxx.xxx.xxx
    username: username
    password: password
---
platform: fos
build_info: 
    # product: fgt  This is not required for FortiGate and FortiFirewall
    repo: AVEngine
    branch: ""
    release: 7
    build: 0
    type: av
    file_pattern: avengine-v7.(.*)-fosv(.*).tgz
device_access: 
    host: xxx.xxx.xxx.xxx
    username: username
    password: password
"""