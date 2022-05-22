package config

import "flag"

var SoftraidDevice = flag.String("softraid-device", "/dev/md0", "Softraid device to monitor")
