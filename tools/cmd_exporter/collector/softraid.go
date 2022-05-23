package collector

import (
	config "cmd_exporter/Config"
	"fmt"
	"os/exec"
	"strconv"
	"strings"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

type SoftraidCollector struct {
	metrics map[string]prometheus.Gauge
}

func (lc *SoftraidCollector) runCommand() map[string]float64 {
	ret := make(map[string]float64)

	cmd := exec.Command(
		"bash", "-c", "mdadm --detail "+*config.SoftraidDevice+" | grep \"Active Devices\\|Working Devices\\|Failed Devices\"",
	)
	dataBytes, err := cmd.Output()
	if err != nil {
		fmt.Println("Error when exec madam command", err.Error())
		return ret
	}
	cmd.Wait()
	data := string(dataBytes)
	data_list := strings.Split(string(data), "\n")

	for _, d := range data_list {
		if d != "" {
			valueList := strings.Split(d, ":")
			if len(valueList) == 2 {
				metrics := strings.ToLower(strings.ReplaceAll(strings.Trim(valueList[0], " "), " ", "_"))
				v, _ := strconv.ParseFloat(strings.Trim(valueList[1], " "), 64)
				ret[metrics] = v
				continue
			}
			fmt.Println("Did not get enough data from cmd,", valueList)
		}
	}

	return ret
}

func (lc *SoftraidCollector) InitMetrics() {
	fmt.Println("Starting softraid Metric")
	data := lc.runCommand()

	lc.metrics = make(map[string]prometheus.Gauge)

	for name, _ := range data {
		fmt.Println("found metrics:", name)
		if name != "" {
			g := promauto.NewGauge(
				prometheus.GaugeOpts{Name: fmt.Sprintf("node_softraid_%s", name)},
			)
			lc.metrics[name] = g
		}
	}

}

func (lc *SoftraidCollector) GetMetrics() {
	data_list := lc.runCommand()
	for name, v := range data_list {
		collector, ok := lc.metrics[name]
		if ok {
			collector.Set(v)
		}
	}
}
