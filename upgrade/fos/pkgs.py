PKGS = {
    "ipssig": {
        # "file": [
        #     "isdb",
        #     "nids",
        #     "apdb"
        # ],
        "cmd_type": "ips",
        "url": "http://172.16.100.71/avqa/ipsSignature/v{release}/",
        "file_name": "{file_lower}_OS{release}_{build}.{file_cap}.pkg"
    },
    "avsig": {
        # "file": [
        #     "ETDB.High",
        #     "FLDB",
        #     "MMDB"
        # ],
        "cmd_type": "av",
        "url": "http://172.16.100.71/avqa/avSignature/FortiGate/v{release}/",
        "file_name": "vsigupdate-OS{release}_{build}.{file}.pkg"
    },
    "malware": {
        # "file": ["latestMalwareFile"],
        "cmd_type": "ips",
        "url": "http://10.160.13.88:8889/sig_eng/ips_sig/malware/",
        "file_name": "{file}_{build}.pkg"
    },
    "ipseng": {
        # "file": ["flen"],
        "cmd_type": "ips",
        "url": "ftp://172.16.100.71/"
               "home/Images/IPSEngine/v{release}/images/build{build}",
        "file_name": "{file_lower}-(.*).pkg",
        "regex": True
    },
    "aveng": {
        # "file": ["vsigupdate"],
        "cmd_type": "av",
        "url": "ftp://172.16.100.71/"
               "home/Images/AVEngine/v{release}/images/build{build}",
        "file_name": "{file_lower}-OS{version}_(.*)_ENG_ALL.pkg",
        "regex": True
    }
}
