package collector

import (
	"fmt"
	"io/ioutil"
	"os/exec"
	"strconv"
	"strings"

	"github.com/prometheus/client_golang/prometheus"
)

type LvmCollector struct {
	dataUsed prometheus.Gauge
	metaUsed prometheus.Gauge
}

func (lc *LvmCollector) InitMetrics() {
	lc.dataUsed = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "node_lvs_data_used_percent",
		Help: "Data used for volume group",
	})
	lc.metaUsed = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "node_lvs_metad_used_percent",
		Help: "Metadata used for volume group",
	})
	prometheus.MustRegister(lc.dataUsed)
	prometheus.MustRegister(lc.metaUsed)
}

func (lc *LvmCollector) GetMetrics() {
	cmd := exec.Command(
		"lvs", "--separator", ",",
		"-o", "data_percent,metadata_percent", "cinder-volumes/cinder-volumes-pool",
	)
	stdout, _ := cmd.StdoutPipe()

	if err := cmd.Start(); err != nil {
		fmt.Println("Error when exec lvs command", err)
	}

	data, err := ioutil.ReadAll(stdout)

	if err != nil {
		fmt.Println("Error when exec lvs command", err)
	}

	out := string(data)
	out_list := strings.Split(out, "\n")[1:]

	if len(out_list) == 2 {
		out = out_list[0]
		out_list = strings.Split(out, ",")

		dataPercent, _ := strconv.ParseFloat(out_list[0], 64)
		metadataPercent, _ := strconv.ParseFloat(out_list[1], 64)
		lc.dataUsed.Set(dataPercent)
		lc.metaUsed.Set(metadataPercent)
	}
}
