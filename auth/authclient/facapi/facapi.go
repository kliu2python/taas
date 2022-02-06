package facapi

import (
	"encoding/base64"
	"fmt"
	"net/http"
	"strings"
)

type FacApiAuthClient struct {
	HttpClient      *http.Client
	CloseConnection bool
	AuthHeader      string
	Url             string
}

func (fa *FacApiAuthClient) SetAuthHeader(admuser, admtoken string) {
	header := fmt.Sprintf("%s:%s", admuser, admtoken)
	header = base64.StdEncoding.EncodeToString([]byte(header))
	fa.AuthHeader = fmt.Sprintf("Basic %s", header)
}

func (fa *FacApiAuthClient) Auth(user, password, token string) (int, error) {
	var payload string
	if token != "" {
		payload = fmt.Sprintf(`
			{
				"username": "%s", 
				"password": "%s",
				"token_code": "%s"
			}`, user, password, token,
		)
	} else {
		payload = fmt.Sprintf(`
			{
				"username": "%s", 
				"password": "%s"
			}`, user, password,
		)
	}
	body := strings.NewReader(payload)
	req, _ := http.NewRequest("POST", fa.Url, body)
	req.Header.Add("Authorization", fa.AuthHeader)
	req.Close = fa.CloseConnection
	resp, err := fa.HttpClient.Do(req)
	if err != nil {
		return 401, err
	}
	defer resp.Body.Close()
	return resp.StatusCode, err
}
