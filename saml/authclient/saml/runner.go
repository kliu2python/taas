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

func (sr *SamlRunner) Run(idx int, c chan []int64) {
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
	SamlClient.EnableRedirectCookie(true)

	t1 := time.Now()
	user := fmt.Sprintf("%s%d", args.USER_PREFIX, idx+1)
	password := args.PASSWORD
	log.Printf(
		"IDX: %d started for Saml, User: %s, Password: %s\n",
		idx, user, password,
	)
	var complete int64 = 0
	var pass int64 = 0
	var fail int64 = 0
	for complete < args.REPEAT {
		SamlClient.InitLogin()
		SamlClient.IdpLogin(user, password)
		status, err := SamlClient.GotoSpPage("Login Successful")
		if args.LOGOUT == true {
			SamlClient.Logoff()
		}
		if status == 200 && err == nil {
			pass++
		} else {
			fail++
		}
		complete++
	}
	t2 := time.Now()
	total := t2.Sub(t1)
	log.Printf(
		"SAML IDX: %d test took %f seconds, %f ms per request",
		idx, total.Seconds(), float64(total.Milliseconds()/args.REPEAT),
	)
	c <- []int64{int64(idx), int64(total.Seconds()), int64(total.Milliseconds() / args.REPEAT), complete, pass, fail}
}
