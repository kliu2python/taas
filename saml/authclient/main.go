package main

import (
	"automation/authclient/args"
	"automation/authclient/facapi"
	"automation/authclient/interfaces"
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

func Run(idx int, c chan interface{}) {
	runner := getRunner()
	runner.Setup(idx)

	var pass int64 = 0
	var fail int64 = 0
	var complete int64
	t1 := time.Now()

	for complete = 0; complete < args.REPEAT; complete++ {
		if runner.Run() == true {
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
	c <- []int64{
		int64(idx),
		int64(total.Seconds()),
		int64(total.Milliseconds() / args.REPEAT),
		complete, pass, fail,
	}
}

func getRunner() interfaces.Runner {
	switch strings.ToLower(args.AUTHMODE) {
	case "saml":
		return &saml.SamlRunner{}
	case "facapi":
		return &facapi.FacApiAuthRunner{}
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
	if args.DISABLE_SSL_VERIFY == true {
		switchOffHttpsVerify()
	}
	dispatchJob()
}
