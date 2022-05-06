package collector

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os/exec"

	"github.com/prometheus/client_golang/prometheus"
)

type NvmeCollector struct {
	metrics map[string]prometheus.G
}

func (lc *NvmeCollector) runCommand() map[string]interface{} {
	cmd := exec.Command(
		"nvme", "smart-log", "/dev/nvme0", "-o", "json",
	)
	stdout, _ := cmd.StdoutPipe()

	if err := cmd.Start(); err != nil {
		fmt.Println("Error when exec nvme command", err)
	}

	data, err := ioutil.ReadAll(stdout)

	var result map[string]interface{}

	if err != nil {
		fmt.Println("Error when exec nvme command", err)
		return result
	}

	dataJson := string(data)

	json.Unmarshal([]byte(dataJson), &result)

	return result
}

func (lc *NvmeCollector) InitMetrics() {
	data := lc.runCommand()
	for key, _ := range data {
		lc.metrics[key] = prometheus.NewGauge(
			prometheus.GaugeOpts{
				Name: fmt.Sprintf("cmd_%s", key),
			},
		)
	}

}

func (lc *NvmeCollector) GetMetrics() {
	data := lc.runCommand()
	for key, value := range data {
		collector := lc.metrics[key]
		collector.Set(value.(string))
	}
}
