package config

import "flag"

var NvmeDevice = flag.String("nvme-device", "/dev/nvme0", "NVME device")
