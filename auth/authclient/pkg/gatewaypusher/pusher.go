package gatewaypusher

import (
	"automation/authclient/args"
	"fmt"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/push"
)

type GateWayPusher struct {
	Pusher    *push.Pusher
	PassGauge prometheus.Gauge
	FailGauge prometheus.Gauge
	Running   bool
	threadID  int
}

func (gw *GateWayPusher) Init(threadID int) *GateWayPusher {
	gw.threadID = threadID

	gw.PassGauge = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "result_pass_count",
		Help: "Test Result Pass Count",
	})
	gw.FailGauge = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "result_fail_count",
		Help: "Test Result Fail Count",
	})

	registry := prometheus.NewRegistry()
	registry.MustRegister(gw.PassGauge, gw.FailGauge)

	gw.Pusher = push.New(
		args.PUSHGATEWAYURL, args.PUSHGATEWAYJOB,
	).Gatherer(registry).Grouping("Thread", fmt.Sprint(gw.threadID))
	gw.Running = true

	go gw.Start()

	return gw
}

func (gw *GateWayPusher) Start() {
	sleepTime := 5 * time.Second

	for {
		if gw.Running {
			gw.PassGauge.Set(float64(3))
			gw.FailGauge.Set(float64(3))

			gw.PassGauge.SetToCurrentTime()
			gw.FailGauge.SetToCurrentTime()

			err := gw.Pusher.Add()
			if err != nil {
				print(err.Error())
			}

			time.Sleep(sleepTime)
		}

	}
}

func (gw *GateWayPusher) Stop() {
	gw.Running = false
}

func New(threadId int) *GateWayPusher {
	gw := GateWayPusher{}
	return gw.Init(threadId)
}
