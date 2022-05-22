package main

import (
	"fmt"
	"io/ioutil"
	"net/http"
	"os/exec"
	"strconv"
	"strings"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	dataUsed = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "node_lvs_data_used_percent",
		Help: "Data used for volume group",
	})
	metaUsed = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "node_lvs_metad_used_percent",
		Help: "Metadata used for volume group",
	})
	volumeCount = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "node_lvs_total_volumes",
		Help: "Total count of created volumes",
	})
)

func GetLvmUsage() {
	cmd := exec.Command(
		"lvs", "--separator", ",",
		"-o", "data_percent,metadata_percent", "cinder-volumes",
	)
	stdout, err := cmd.StdoutPipe()

	if err != nil {
		fmt.Println("Error when exec lvs command", err)
	}

	if err := cmd.Start(); err != nil {
		fmt.Println("Error when exec lvs command", err)
	}

	data, err := ioutil.ReadAll(stdout)

	if err != nil {
		fmt.Println("Error when exec lvs command", err)
	}

	out := string(data)
	out_list := strings.Split(out, "\n")[1:]

	if len(out_list) >= 2 {
		out = out_list[0]
		out_list_vg := strings.Split(out, ",")

		dataPercent, _ := strconv.ParseFloat(strings.Trim(out_list_vg[0], " "), 64)
		metadataPercent, _ := strconv.ParseFloat(strings.Trim(out_list_vg[1], " "), 64)
		dataUsed.Set(dataPercent)
		metaUsed.Set(metadataPercent)
		volumeCount.Set(float64(len(out_list) - 2))
		return
	}
	dataUsed.Set(-1)
	metaUsed.Set(-1)
	volumeCount.Set(-1)
}

func main() {
	prometheus.MustRegister(dataUsed)
	prometheus.MustRegister(metaUsed)
	prometheus.MustRegister(volumeCount)

	go func() {
		for {
			GetLvmUsage()
			time.Sleep(time.Second * 5)
		}
	}()
	http.Handle("/metrics", promhttp.Handler())
	http.ListenAndServe(":9898", nil)
}
