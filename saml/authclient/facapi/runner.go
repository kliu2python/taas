package facapi

import (
	"automation/authclient/args"
	"fmt"
	"log"
	"net/http"
)

type FacApiAuthRunner struct {
	AuthClient *FacApiAuthClient
	UserName   string
	Password   string
}

func (r *FacApiAuthRunner) Setup(idx int) {
	r.AuthClient = &FacApiAuthClient{
		HttpClient: &http.Client{},
		Url:        args.URL,
	}

	r.AuthClient.SetAuthHeader(args.FAC_ADMIN_USER, args.FAC_ADMIN_TOKEN)

	r.UserName = fmt.Sprintf("%s%d", args.USER_PREFIX, idx+1)
	r.Password = args.PASSWORD
	log.Printf(
		"IDX: %d Setup for FAC API Auth, User: %s, Password: %s\n",
		idx, r.UserName, r.Password,
	)
}

func (r *FacApiAuthRunner) Run() bool {
	code, err := r.AuthClient.Auth(r.UserName, r.Password, "")
	if err != nil {
		log.Printf("Login Error, %v\n", err)
		return false
	}
	if code == 200 {
		return true
	}
	log.Printf("Login Failed, %v\n", code)
	return false
}
