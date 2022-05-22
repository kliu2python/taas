package collector

import (
	config "cmd_exporter/Config"
	"fmt"
	"io/ioutil"
	"os/exec"
	"strconv"
	"strings"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

type LvmCollector struct {
	dataUsed    prometheus.Gauge
	metaUsed    prometheus.Gauge
	volumeCount prometheus.Gauge
}

func (lc *LvmCollector) InitMetrics() {
	lc.dataUsed = promauto.NewGauge(prometheus.GaugeOpts{
		Name: "node_lvs_data_used_percent",
		Help: "Data used for volume group",
	})
	lc.metaUsed = promauto.NewGauge(prometheus.GaugeOpts{
		Name: "node_lvs_metad_used_percent",
		Help: "Metadata used for volume group",
	})
	lc.volumeCount = promauto.NewGauge(prometheus.GaugeOpts{
		Name: "node_lvs_total_volumes",
		Help: "Total count of created volumes",
	})
}

func (lc *LvmCollector) GetMetrics() {
	cmd := exec.Command(
		"lvs", "--separator", ",",
		"-o", "data_percent,metadata_percent", *config.VolumeGroupName,
	)
	stdout, _ := cmd.StdoutPipe()

	if err := cmd.Start(); err != nil {
		fmt.Println("Error when exec lvs command", err)
	}

	data, err := ioutil.ReadAll(stdout)

	if err != nil {
		fmt.Println("Error when exec lvs command", err)
	}
	cmd.Wait()
	out := string(data)
	out_list := strings.Split(out, "\n")[1:]

	if len(out_list) >= 2 {
		out = out_list[0]
		out_list_gv := strings.Split(out, ",")

		dataPercent, _ := strconv.ParseFloat(strings.Trim(out_list_gv[0], " "), 64)
		metadataPercent, _ := strconv.ParseFloat(strings.Trim(out_list_gv[1], " "), 64)

		lc.volumeCount.Set(float64(len(out_list) - 2))
		lc.dataUsed.Set(dataPercent)
		lc.metaUsed.Set(metadataPercent)
	}
}
