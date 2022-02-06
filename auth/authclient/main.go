package main

import (
	"automation/authclient/args"
	"automation/authclient/facapi"
	"automation/authclient/interfaces"
	"automation/authclient/oauth"
	"automation/authclient/pkg/taas"
	"automation/authclient/saml"
	"crypto/tls"
	"log"
	"net/http"
	"strings"
	"time"
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
	var complete int64
	t1 := time.Now()
	for complete = 0; complete < args.REPEAT; complete++ {
		if runner.Run() {
			pass++
		} else {
			fail++
		}
	}

	t2 := time.Now()
	total := t2.Sub(t1)
	log.Printf(
		"%s IDX: %d test took %f seconds, %f ms per request",
		args.AUTHMODE, idx, total.Seconds(), float64(total.Milliseconds()/args.REPEAT),
	)
	if rm != nil {
		rm.Release()
	}
	c <- []int64{
		int64(idx),
		int64(total.Seconds()),
		int64(total.Milliseconds() / args.REPEAT),
		complete, pass, fail,
	}
}

// Due to API Call count per second limit on FAC, facapi will not support signle
// Thread for now
func getRunner() interfaces.Runner {
	switch strings.ToLower(args.AUTHMODE) {
	case "saml":
		return &saml.SamlRunner{}
	case "facapi":
		return &facapi.FacApiAuthRunner{}
	case "oauthtoken":
		return &oauth.OauthTokenRunner{}
	default:
		return &saml.SamlRunner{}
	}
}

func dispatchJob() {
	c := make(chan interface{})
	for i := 0; i < args.CONCURRENT; i++ {
		go Run(i, c)
	}
	for i := 0; i < args.CONCURRENT; i++ {
		log.Printf("%v\n", <-c)
	}
}

func main() {
	if args.DISABLE_SSL_VERIFY {
		switchOffHttpsVerify()
	}
	dispatchJob()
}
