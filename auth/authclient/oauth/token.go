package oauth

import (
	"automation/authclient/pkg/apiclient"
	"automation/authclient/pkg/otp"
	"fmt"
	"net/http"
	"strings"
)

type OauthTokenClient struct {
	ClientId     string
	ClientSecret string
	GrantType    string
	FacIp        string
	requestUrl   string
	verifyUrl    string
	revokeUrl    string
	ApiClient    *apiclient.ApiClient
}

type Token struct {
	AccessToken  string `json:"access_token"`
	ExpireIn     int    `json:"expires_in"`
	TokenType    string `json:"token_type"`
	Scope        string `json:"scope"`
	RefreshToken string `json:"refresh_token"`
}

type TokenVerification struct {
	ExpireIn int    `json:"expires_in"`
	UserName string `json:"username"`
}

func (oc *OauthTokenClient) InitClient() {
	oc.requestUrl = fmt.Sprintf("https://%s/api/v1/oauth/token/", oc.FacIp)
	oc.verifyUrl = fmt.Sprintf(
		"https://%s/api/v1/oauth/verify_token/?client_id=%s", oc.FacIp, oc.ClientId,
	)
	oc.revokeUrl = fmt.Sprintf("https://%s/api/v1/oauth/revoke_token/", oc.FacIp)
}

func (oc *OauthTokenClient) GetToken(user, password, seed string) (*Token, error) {
	var tokenField string
	if len(seed) > 0 {
		token := otp.GetOtp(seed)
		tokenField = fmt.Sprintf(
			`
			"challenge": "otp",
			"challenge_response": "%s",
			"method": "ftm",
			`, token,
		)
	} else {
		tokenField = ""
	}

	body := strings.NewReader(fmt.Sprintf(`
		{
			"username": "%s",
			"password": "%s",
			"client_id": "%s",
			"client_secret": "%s",
			%s
			"grant_type": "%s"
		}
	`, user, password, oc.ClientId, oc.ClientSecret, tokenField, oc.GrantType))
	response := Token{}
	return &response, oc.ApiClient.Call("POST", oc.requestUrl, nil, body, 200, &response)
}

func (oc *OauthTokenClient) VerifyToken(token *Token) error {
	header := http.Header{}
	header.Add("Authorization", fmt.Sprintf("%s %s", token.TokenType, token.AccessToken))
	verification := &TokenVerification{}
	err := oc.ApiClient.Call("GET", oc.verifyUrl, &header, nil, 200, verification)
	if err != nil {
		return err
	}
	if len(verification.UserName) > 0 {
		return nil
	}
	return fmt.Errorf("failed to verify user in response, %s", verification.UserName)
}

func (oc *OauthTokenClient) RevokeToken(token *Token) error {
	body := strings.NewReader(fmt.Sprintf(`
		{
			"token": "%s",
			"client_id": "%s",
			"client_secret": "%s"
		}
	`, token.AccessToken, oc.ClientId, oc.ClientSecret),
	)
	return oc.ApiClient.Call("POST", oc.revokeUrl, nil, body, 200, nil)
}
