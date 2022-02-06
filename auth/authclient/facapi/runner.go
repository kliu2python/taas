package facapi

import (
	"automation/authclient/args"
	"automation/authclient/pkg/otp"
	"automation/authclient/pkg/taas"
	"fmt"
	"log"
	"net/http"
)

type FacApiAuthRunner struct {
	AuthClient      *FacApiAuthClient
	ResourceManager *taas.ResourceManager
	Password        string
	BaseName        string
	Idx             int
	IdxMin          int
	IdxSize         int
}

func (r *FacApiAuthRunner) Setup(idx int, rm *taas.ResourceManager) {
	var Url string
	if len(args.URL) == 0 {
		Url = fmt.Sprintf("https://%s/api/v1/auth/", args.AUTH_SERVER_IP)
	} else {
		Url = args.URL
	}
	r.AuthClient = &FacApiAuthClient{
		HttpClient:      &http.Client{},
		Url:             Url,
		CloseConnection: args.CLOSE_CONNECTION,
	}

	r.AuthClient.SetAuthHeader(args.FAC_ADMIN_USER, args.FAC_ADMIN_TOKEN)
	r.IdxMin = idx * args.FAC_USER_IDX_SLICE
	r.IdxSize = r.IdxMin + args.FAC_USER_IDX_SLICE
	r.Password = args.PASSWORD
	r.BaseName = args.USER_PREFIX
	if rm != nil {
		r.ResourceManager = rm
	}
	log.Printf("IDX: %d Setup for FAC API Auth\n", idx)
}

func (r *FacApiAuthRunner) Run() bool {
	var user, password, seed string
	if r.ResourceManager == nil {
		if r.Idx < r.IdxSize {
			r.Idx++
		} else {
			r.Idx = r.IdxMin + 1
		}
		user = fmt.Sprintf("%s%d", r.BaseName, r.Idx)
		password = r.Password
		seed = ""
	} else {
		res, err := r.ResourceManager.Get()
		if res == nil {
			fmt.Printf("No Resource get, error: %v", err)
			return false
		}
		user = res.User
		password = res.Password

		r.AuthClient.SetAuthHeader(res.CustomData.FacAdminUser, res.CustomData.FacAdminToken)
		seed = res.Seed
	}
	token := ""
	if seed != "" {
		token = otp.GetOtp(seed)
	}
	code, err := r.AuthClient.Auth(user, password, token)

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
