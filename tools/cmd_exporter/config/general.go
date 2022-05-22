package config

import "flag"

var Collectors = flag.String("collectors", "",
	`Collectors to enable, comma seperated for different engines
	supported engines: 
	
	lvs: for lvm collector
	nvme: for nvme collector
	softraid: for softraid collector
	
	usage: cmd_exporter lvs,nvme,softraid xx`,
)
var CollectInterval = flag.Int("interval", 5, "collect internal in second")
