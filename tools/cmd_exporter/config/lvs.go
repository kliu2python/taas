package config

import "flag"

var VolumeGroupName = flag.String("volume-group", "cinder-volumes", "volume group to monitor")
