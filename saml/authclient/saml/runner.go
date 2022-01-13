package saml

import (
	"automation/authclient/args"
	"fmt"
	"log"
	"net/http"
	"net/http/cookiejar"
)

type SamlRunner struct {
	SamlClient *SamlClient
	UserName   string
	Password   string
}

func (sr *SamlRunner) Setup(idx int) {
	jar, err := cookiejar.New(nil)
	if err != nil {
		log.Fatal(err)
	}
	sr.SamlClient = &SamlClient{
		HttpClient: &http.Client{
			Jar: jar,
		},
		Url: args.URL,
	}

	sr.UserName = fmt.Sprintf("%s%d", args.USER_PREFIX, idx+1)
	sr.Password = args.PASSWORD
	log.Printf(
		"IDX: %d Setup for Saml, User: %s, Password: %s\n",
		idx, sr.UserName, sr.Password,
	)
}

func (sr *SamlRunner) Run() bool {
	code, err := sr.SamlClient.InitLogin()
	result := true
	if err != nil || code != 200 {
		log.Printf("Init Login Error, code: %d, error: %v", code, err)
		result = false
	}

	code, err = sr.SamlClient.IdpLogin(sr.UserName, sr.Password)
	if err != nil || code != 200 {
		log.Printf("Idp Login Error, code: %d, error: %v", code, err)
		result = false
	}

	code, err = sr.SamlClient.GotoSpPage("Login Successful")
	if err != nil || code != 200 {
		log.Printf("Page Launch Error, code: %d, error: %v", code, err)
		result = false
	}

	if args.LOGOUT == true {
		code, err = sr.SamlClient.Logoff()
		if err != nil || code != 200 {
			log.Printf("Logoff Error, code: %d, error: %v", code, err)
			result = false
		}
	}

	return result
}
