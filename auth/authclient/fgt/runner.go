package fgt

import (
	"automation/authclient/pkg/otp"
	"automation/authclient/pkg/taas"
	"automation/authclient/pkg/utils"
	"fmt"
	"log"
)

type SslVpnRunner struct {
	SslVpnClient    *SslVpnClient
	ResourceManager *taas.ResourceManager
	UserName        string
	Password        string
	SslVpnUrl       string
}

func (sr *SslVpnRunner) Setup(idx int, rm *taas.ResourceManager) {
	sr.SslVpnClient = &SslVpnClient{}
	sr.SslVpnClient.GetHttpClient()
	sr.ResourceManager = rm
	log.Printf(
		"IDX: %d Setup for Saml\n", idx,
	)
}

func (r *SslVpnRunner) Run() bool {
	defer utils.CatchError()

	res, err := r.ResourceManager.Get()
	if res == nil {
		fmt.Printf("No Resource get, error: %v", err)
		return false
	}
	user := res.User
	password := res.Password
	seed := res.Seed
	url := res.CustomData.FgtSslVpnUrl

	code, context := r.SslVpnClient.Login(url, user, password, "", "")

	if code != 200 {
		log.Printf("Login Error, code: %d, user: %v, error: %v", code, user, context)
		return false
	}
	if len(seed) > 0 {
		token := otp.GetOtp(seed)
		code, context = r.SslVpnClient.Login(url, user, password, token, context)
	}
	if code != 200 {
		log.Printf("Token Login Error, code: %d, error: %v", code, context)
		return false
	}
	return true
}
