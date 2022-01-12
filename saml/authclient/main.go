package main

import (
	"automation/authclient/args"
	"automation/authclient/interfaces"
	"automation/authclient/saml"
	"crypto/tls"
	"log"
	"net/http"
	"strings"
)

func switchOffHttpsVerify() {
	http.DefaultTransport.(*http.Transport).TLSClientConfig =
		&tls.Config{InsecureSkipVerify: true}
}

func getRunner() interfaces.Runner {
	switch strings.ToLower(args.AUTHMODE) {
	case "saml":
		return &saml.SamlRunner{}
	default:
		return &saml.SamlRunner{}
	}
}

func dispatchJob(runner interfaces.Runner) {
	c := make(chan []int64)
	for i := 0; i < args.CONCURRENT; i++ {
		go runner.Run(i, c)
	}
	for i := 0; i < args.CONCURRENT; i++ {
		log.Printf("%v\n", <-c)
	}
}

func main() {
	if args.DISABLE_SSL_VERIFY == true {
		switchOffHttpsVerify()
	}
	runner := getRunner()
	dispatchJob(runner)
}
