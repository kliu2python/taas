package oauth

import (
	"automation/authclient/args"
	"automation/authclient/pkg/apiclient"
	"fmt"
	"log"
	"net/http"
)

type OauthTokenRunner struct {
	OauthTokenClient *OauthTokenClient
	UserName         string
	Password         string
}

func (r *OauthTokenRunner) Setup(idx int) {
	r.UserName = fmt.Sprintf("%s%d", args.USER_PREFIX, idx)
	r.Password = args.PASSWORD
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
	token, err := r.OauthTokenClient.GetToken(r.UserName, r.Password)
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
