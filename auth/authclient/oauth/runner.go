package oauth

import (
	"automation/authclient/args"
	"automation/authclient/pkg/apiclient"
	"automation/authclient/pkg/taas"
	"automation/authclient/pkg/utils"
	"fmt"
	"log"
	"net/http"
)

type OauthTokenRunner struct {
	OauthTokenClient *OauthTokenClient
	ResourceManager  *taas.ResourceManager
	UserName         string
	Password         string
}

func (r *OauthTokenRunner) Setup(idx int, rm *taas.ResourceManager) {
	r.UserName = fmt.Sprintf("%s%d", args.USER_PREFIX, idx)
	r.Password = args.PASSWORD
	r.ResourceManager = rm
	apiClient := &apiclient.ApiClient{
		HttpClient:      &http.Client{},
		CloseConnection: args.CLOSE_CONNECTION,
	}
	r.OauthTokenClient = &OauthTokenClient{
		ClientId:     args.OAUTH_CLIENT_ID,
		ClientSecret: args.OAUTH_CLIENT_SECRET,
		GrantType:    args.OAUTH_GRANT_TYPE,
		FacIp:        args.AUTH_SERVER_IP,
		ApiClient:    apiClient,
	}
	r.OauthTokenClient.InitClient()
}

func (r *OauthTokenRunner) Run() bool {
	defer utils.CatchError()
	var user, password, seed string
	if r.ResourceManager == nil {
		user = r.UserName
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
		seed = res.Seed
		r.OauthTokenClient.ClientId = res.CustomData.OauthClientId
		r.OauthTokenClient.ClientSecret = res.CustomData.OauthClientSecret
		r.OauthTokenClient.FacIp = res.CustomData.FacIp
		r.OauthTokenClient.InitClient()
	}

	token, err := r.OauthTokenClient.GetToken(user, password, seed)
	if err != nil {
		log.Printf("Get Token Error, %v\n", err)
		return false
	}
	err = r.OauthTokenClient.VerifyToken(token)
	if err != nil {
		log.Printf("Verify Token Error, %v\n", err)
		return false
	}
	err = r.OauthTokenClient.RevokeToken(token)
	if err != nil {
		log.Printf("Revoke Token Error, %v\n", err)
		return false
	}
	return true
}
