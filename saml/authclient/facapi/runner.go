package facapi

import (
	"automation/authclient/args"
	"fmt"
	"log"
	"net/http"
)

type FacApiAuthRunner struct {
	AuthClient *FacApiAuthClient
	Password   string
	BaseName   string
	Idx        int
	IdxMin     int
	IdxSize    int
}

func (r *FacApiAuthRunner) Setup(idx int) {
	r.AuthClient = &FacApiAuthClient{
		HttpClient: &http.Client{},
		Url:        args.URL,
	}

	r.AuthClient.SetAuthHeader(args.FAC_ADMIN_USER, args.FAC_ADMIN_TOKEN)
	r.IdxMin = idx * args.FAC_USER_IDX_SLICE
	r.IdxSize = r.IdxMin + args.FAC_USER_IDX_SLICE
	r.Password = args.PASSWORD
	r.BaseName = args.USER_PREFIX
	log.Printf(
		"IDX: %d Setup for FAC API Auth, User: %s, Password: %s\n",
		idx, r.BaseName, r.Password,
	)
}

func (r *FacApiAuthRunner) Run() bool {
	if r.Idx < r.IdxSize {
		r.Idx++
	} else {
		r.Idx = r.IdxMin + 1
	}
	user := fmt.Sprintf("%s%d", r.BaseName, r.Idx)
	code, err := r.AuthClient.Auth(user, r.Password, "")
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
