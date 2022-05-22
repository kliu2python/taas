package main

import (
	config "cmd_exporter/Config"
	"cmd_exporter/collector"
	"flag"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var Collectors []collector.Collector

func registerCollectors() {
	Collectors = []collector.Collector{}

	if *config.Collectors == "" {
		log.Print("Collect Engine is not specified")
		os.Exit(1)
	}

	collectorsList := strings.Split(*config.Collectors, ",")

	for _, col := range collectorsList {
		switch col {
		case "lvs":
			Collectors = append(Collectors, &collector.LvmCollector{})
		case "nvme":
			Collectors = append(Collectors, &collector.NvmeCollector{})
		case "softraid":
			Collectors = append(Collectors, &collector.SoftraidCollector{})
		default:
			log.Panicf("Unknown collect engine: %s", col)
		}
	}
}

func initMetrics() {
	for _, col := range Collectors {
		col.InitMetrics()
	}
}

func getMetrics() {
	for _, col := range Collectors {
		col.GetMetrics()
	}
}

func collect() {
	go func() {
		for {
			getMetrics()
			time.Sleep(time.Second * time.Duration(*config.CollectInterval))
		}
	}()
}

func main() {
	flag.Parse()

	registerCollectors()
	initMetrics()

	collect()

	http.Handle("/metrics", promhttp.Handler())
	http.ListenAndServe(":9898", nil)
}
