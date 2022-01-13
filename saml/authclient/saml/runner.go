package saml

import (
	"automation/authclient/args"
	"fmt"
	"log"
	"net/http"
	"net/http/cookiejar"
	"time"
)

type SamlRunner struct{}

func (sr *SamlRunner) Run(idx int, c chan interface{}) {
	jar, err := cookiejar.New(nil)
	if err != nil {
		log.Fatal(err)
	}
	SamlClient := SamlClient{
		HttpClient: &http.Client{
			Jar: jar,
		},
		Url: args.URL,
	}

	user := fmt.Sprintf("%s%d", args.USER_PREFIX, idx+1)
	password := args.PASSWORD
	log.Printf(
		"IDX: %d started for Saml, User: %s, Password: %s\n",
		idx, user, password,
	)

	var pass int64 = 0
	var fail int64 = 0
	var complete int64
	t1 := time.Now()

	for complete = 0; complete < args.REPEAT; complete++ {
		code, err := SamlClient.InitLogin()
		has_fail := false
		if err != nil || code != 200 {
			log.Printf("Init Login Error, code: %d, error: %v", code, err)
			has_fail = true
		}

		code, err = SamlClient.IdpLogin(user, password)
		if err != nil || code != 200 {
			log.Printf("Idp Login Error, code: %d, error: %v", code, err)
			has_fail = true

		}

		code, err = SamlClient.GotoSpPage("Login Successful")
		if err != nil || code != 200 {
			log.Printf("Page Launch Error, code: %d, error: %v", code, err)
			has_fail = true

		}

		if args.LOGOUT == true {
			code, err = SamlClient.Logoff()
			if err != nil || code != 200 {
				log.Printf("Logoff Error, code: %d, error: %v", code, err)
				has_fail = true
			}
		}
		if has_fail {
			fail++
		} else {
			pass++
		}
	}

	t2 := time.Now()
	total := t2.Sub(t1)
	log.Printf(
		"SAML IDX: %d test took %f seconds, %f ms per request",
		idx, total.Seconds(), float64(total.Milliseconds()/args.REPEAT),
	)
	c <- []int64{int64(idx), int64(total.Seconds()), int64(total.Milliseconds() / args.REPEAT), complete, pass, fail}
}
