package main

import (
	"automation/authclient/args"
	"automation/authclient/facapi"
	"automation/authclient/fgt"
	"automation/authclient/interfaces"
	"automation/authclient/oauth"
	"automation/authclient/pkg/gatewaypusher"
	"automation/authclient/pkg/taas"
	"automation/authclient/saml"
	"crypto/tls"
	"fmt"
	"net/http"
	"strings"
	"time"

	log "github.com/sirupsen/logrus"
)

func switchOffHttpsVerify() {
	http.DefaultTransport.(*http.Transport).TLSClientConfig =
		&tls.Config{InsecureSkipVerify: true}
}

// func syncRun() {
// 	client, err := pulsar.NewClient(pulsar.ClientOptions{
// 		URL:               "pulsar://localhost:6650,localhost:6651,localhost:6652",
// 		OperationTimeout:  30 * time.Second,
// 		ConnectionTimeout: 30 * time.Second,
// 	})
// 	if err != nil {
// 		log.Fatalf("Could not instantiate Pulsar client: %v", err)
// 	}

// 	defer client.Close()
// }

func Run(idx int, c chan interface{}) {
	var rm *taas.ResourceManager
	if args.USE_TAAS {
		rm = &taas.ResourceManager{}
		rm.Init(args.TAAS_IP)
		rm.Request(args.RESOURCE_POOL_SIZE, args.RESOURCE_POOL_NAME)
	} else {
		rm = nil
	}

	runner := getRunner()
	runner.Setup(idx, rm)

	var pass int64 = 0
	var fail int64 = 0
	var complete int64 = 0
	var lastComplete int64 = 0
	var interval int64 = int64(args.REPORT_INTERVAL)

	t1 := time.Now()
	for ; complete < args.REPEAT; complete++ {
		if runner.Run() {
			pass++
		} else {
			fail++
		}
		if complete > 0 && complete%interval == 0 {
			t2 := time.Now()
			total := t2.Sub(t1)
			c <- []int64{
				int64(idx),
				t2.Unix(),
				int64(total.Seconds()),
				int64(total.Milliseconds() / (complete - lastComplete)),
				complete,
				pass,
				fail,
			}
			lastComplete = complete
			t1 = time.Now()
		}

	}

	if rm != nil {
		rm.Release()
	}

	c <- []int64{}
}

// Due to API Call count per second limit on FAC, facapi will not support signle
// Thread for now
func getRunner() interfaces.Runner {
	switch strings.ToLower(args.AUTHMODE) {
	case "facapi":
		return &facapi.FacApiAuthRunner{}
	case "oauthtoken":
		return &oauth.OauthTokenRunner{}
	case "sslvpn":
		return &fgt.SslVpnRunner{}
	default:
		return &saml.SamlRunner{}
	}
}

func dispatchJob() {
	c := make(chan interface{}, 1024)
	for i := 0; i < args.CONCURRENT; i++ {
		go Run(i, c)
	}

	var stopped int = 0
	pusher := gatewaypusher.GateWayRabbit{}

	if args.PUSH_DATA {
		pusher.Connect()
		pusher.PrepareData(args.CONCURRENT)
	}

	for {
		v := (<-c).([]int64)
		if len(v) == 0 {
			stopped++
			if stopped == args.CONCURRENT {
				break
			}
		}
		if args.PUSH_DATA {
			pusher.Push(v)
		}

		log.Debug(
			fmt.Sprintf("%s IDX: %d, %d test took %d seconds, %d ms per request, pass: %d, fail: %d",
				args.AUTHMODE, v[0], v[4], v[2], v[3], v[5], v[6],
			),
		)
	}
}

func main() {
	if args.DISABLE_SSL_VERIFY {
		switchOffHttpsVerify()
	}
	logLevel := log.InfoLevel
	if args.LOG_LEVEL == "debug" {
		logLevel = log.DebugLevel
	}
	log.SetLevel(logLevel)
	dispatchJob()
}
