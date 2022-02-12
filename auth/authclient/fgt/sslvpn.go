package fgt

import (
	"automation/authclient/pkg/pageclient"
	"fmt"
	"io"
	"net/http"
	"strings"
)

type SslVpnClient struct {
	pageclient.PageClient
	lastLoginUrl string
}

func (sc *SslVpnClient) Login(url, username, password, code, context string) (int, string) {
	if sc.lastLoginUrl != "" {
		sc.Logout()
	}
	var body *strings.Reader
	sc.lastLoginUrl = url
	url = fmt.Sprintf("%s/remote/logincheck", strings.Trim(url, "/"))
	if len(code) > 0 {
		body = strings.NewReader(
			fmt.Sprintf("%s&ajax=1&username=%s&realm=&credential=%s&code=%s", context, username, password, code),
		)
	} else {
		body = strings.NewReader(
			fmt.Sprintf("ajax=1&username=%s&realm=&credential=%s", username, password),
		)
	}
	resp, err := sc.HttpClient.Post(url, "text/plain", body)
	if err != nil || resp.StatusCode != 200 {
		return 401, fmt.Sprintf("Failed to init login, %v", err)
	}
	defer resp.Body.Close()
	content, _ := io.ReadAll(resp.Body)
	ret_str := string(content)
	if strings.Contains(ret_str, "permission_denied") {
		return 401, fmt.Sprintf("permission_denied, user: %s", username)
	}
	return resp.StatusCode, strings.ReplaceAll(ret_str, ",", "&")
}

func (sc *SslVpnClient) Logout() (int, string) {
	url := fmt.Sprintf("%s/remote/logout", strings.Trim(sc.lastLoginUrl, "/"))
	resp, err := sc.HttpClient.Post(url, "text/plain", http.NoBody)
	if err != nil {
		return 400, fmt.Sprintf("Logout Error , error: %v, url: %v", err, sc.lastLoginUrl)
	}
	sc.lastLoginUrl = ""
	return resp.StatusCode, "Logout Success"
}
