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
)

func GetLvmUsage() (float64, float64) {
	cmd := exec.Command(
		"lvs", "--separator", ",",
		"-o", "data_percent,metadata_percent", "cinder-volumes/cinder-volumes-pool",
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

	if len(out_list) == 2 {
		out = out_list[0]
		out_list = strings.Split(out, ",")

		dataPercent, _ := strconv.ParseFloat(out_list[0], 64)
		metadataPercent, _ := strconv.ParseFloat(out_list[1], 64)
		return dataPercent, metadataPercent
	}
	return -1, -1
}

func main() {
	prometheus.MustRegister(dataUsed)
	prometheus.MustRegister(metaUsed)

	go func() {
		for {
			data, meta := GetLvmUsage()

			dataUsed.Set(data)
			metaUsed.Set(meta)
			time.Sleep(time.Second * 5)
		}
	}()

	http.Handle("/metrics", promhttp.Handler())
	http.ListenAndServe(":9898", nil)
}
