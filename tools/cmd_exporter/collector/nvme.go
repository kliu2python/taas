package collector

import (
	config "cmd_exporter/Config"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os/exec"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

type NvmeCollector struct {
	metrics map[string]prometheus.Gauge
}

func (lc *NvmeCollector) runCommand() map[string]interface{} {
	cmd := exec.Command(
		"nvme", "smart-log", *config.NvmeDevice, "-o", "json",
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
	cmd.Wait()
	dataJson := string(data)

	json.Unmarshal([]byte(dataJson), &result)

	return result
}

func (lc *NvmeCollector) InitMetrics() {
	data := lc.runCommand()

	lc.metrics = make(map[string]prometheus.Gauge)

	for key, _ := range data {
		metricName := fmt.Sprintf("node_nvme_%s", key)
		g := promauto.NewGauge(
			prometheus.GaugeOpts{
				Name: metricName,
			},
		)
		lc.metrics[key] = g
	}

}

func (lc *NvmeCollector) GetMetrics() {
	data := lc.runCommand()
	for key, value := range data {
		collector, ok := lc.metrics[key]
		if ok {
			collector.Set(float64(value.(float64)))
		}
	}
}
