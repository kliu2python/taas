package saml

import (
	"automation/authclient/args"
	"automation/authclient/pkg/taas"
	"automation/authclient/pkg/utils"
	"fmt"
	"log"
	"net/http"
	"net/http/cookiejar"
)

type SamlRunner struct {
	SamlClient      *SamlClient
	ResourceManager *taas.ResourceManager
	UserName        string
	Password        string
}

func (sr *SamlRunner) Setup(idx int, rm *taas.ResourceManager) {
	jar, err := cookiejar.New(nil)
	if err != nil {
		log.Fatal(err)
	}
	sr.SamlClient = &SamlClient{
		HttpClient: &http.Client{
			Jar: jar,
		},
	}

	sr.UserName = fmt.Sprintf("%s%d", args.USER_PREFIX, idx+1)
	sr.Password = args.PASSWORD
	sr.ResourceManager = rm
	log.Printf(
		"IDX: %d Setup for Saml\n", idx,
	)
}

func (r *SamlRunner) Run() bool {
	defer utils.CatchError()

	var user, password, seed, url string
	if r.ResourceManager == nil {
		user = r.UserName
		password = r.Password
		url = args.URL
		seed = ""
	} else {
		res, err := r.ResourceManager.Get()
		if res == nil {
			fmt.Printf("No Resource get, error: %v", err)
			return false
		}
		user = res.User
		password = res.Password
		seed = res.Seed
		url = res.CustomData.SamlSpUrl
	}

	code, err := r.SamlClient.InitLogin(url)

	if err != nil || code != 200 {
		log.Printf("Init Login Error, code: %d, error: %v", code, err)
		return false
	}

	code, err = r.SamlClient.IdpLogin(user, password, seed)
	if err != nil || code != 200 {
		log.Printf("Idp Login Error, code: %d, error: %v", code, err)
		return false
	}

	code, err = r.SamlClient.GotoSpPage("Login Successful")
	if err != nil || code != 200 {
		log.Printf("Page Launch Error, code: %d, error: %v", code, err)
		return false
	}

	if args.LOGOUT {
		code, err = r.SamlClient.Logoff()
		if err != nil || code != 200 {
			log.Printf("Logoff Error, code: %d, error: %v", code, err)
			return false
		}
	}
	return true
}
