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

func (lc *SoftraidCollector) runCommand() string {
	data, err := exec.Command(
		"bash", "-c", "mdadm --detail "+*config.SoftraidDevice+" | grep \"Active Devices\\|Working Devices\\|Failed Devices\"",
	).Output()

	if err != nil {
		fmt.Println("Error when exec madam command", err.Error())
		return err.Error()
	}

	return string(data)
}

func (lc *SoftraidCollector) getMetricName(in string) string {
	d := ""
	if in != "\n" {
		d = strings.ToLower(strings.ReplaceAll(strings.Trim(in, " "), " ", "_"))
		d = fmt.Sprintf("node_softraid_%s", d)
	}
	return d
}

func (lc *SoftraidCollector) InitMetrics() {
	data := lc.runCommand()
	data_list := strings.Split("\n", data)
	fmt.Println(data_list)
	lc.metrics = make(map[string]prometheus.Gauge)

	for _, d := range data_list {
		d = strings.Split(d, ":")[0]
		d = lc.getMetricName(d)
		fmt.Println("found name:", d)
		if d != "" {
			g := promauto.NewGauge(
				prometheus.GaugeOpts{Name: d},
			)
			lc.metrics[d] = g
		}
	}

}

func (lc *SoftraidCollector) GetMetrics() {
	data := lc.runCommand()
	data_list := strings.Split("\n", data)
	for _, d := range data_list {
		if d == "\n" {
			continue
		}
		dl := strings.Split(d, ":")
		d = dl[0]
		v := dl[1]
		d = lc.getMetricName(d)
		if d != "" {
			collector, ok := lc.metrics[d]
			if ok {
				v, _ := strconv.ParseFloat(v, 64)
				collector.Set(v)
			}
		}
	}
}
