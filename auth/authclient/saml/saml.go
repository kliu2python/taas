package saml

import (
	"bufio"
	"errors"
	"fmt"
	"io"
	"io/ioutil"
	"net/http"
	"net/url"
	"strings"

	"automation/authclient/pkg/otp"
	"automation/authclient/pkg/xmlparser"
)

type SamlClient struct {
	HttpClient    *http.Client
	Url           string
	CsfrToken     string
	Cookie        string
	InitCookie    string
	LogoutToken   string
	AcsUrl        string
	AcsMethod     string
	HandleCookie  bool
	Redirect      bool
	SamlAssertion url.Values
}

// func printBody(body io.ReadCloser) {
// 	b, _ := io.ReadAll(body)
// 	fmt.Printf("%s", b)
// }

func (sd *SamlClient) purifyCookie(cookie string) string {
	return strings.Split(cookie, ";")[0]
}

func (sd *SamlClient) updateCSRFToken(body io.ReadCloser) {
	buf := bufio.NewReaderSize(body, 65536)
	parser := xmlparser.NewXMLParser(buf, "input").ParseAttributesOnly("input")
	for xml := range parser.Stream() {
		if xml.Attrs["name"] == "csrfmiddlewaretoken" {
			sd.CsfrToken = xml.Attrs["value"]
			break
		}
	}
}

func (sd *SamlClient) InitLogin(url string) (int, error) {
	sd.DisableRedirectCookie()
	sd.EnableRedirect()
	resp, err := sd.HttpClient.Get(url)
	if err != nil || resp.StatusCode > 399 {
		return resp.StatusCode, err
	}
	defer resp.Body.Close()
	sd.Cookie = sd.purifyCookie(resp.Header["Set-Cookie"][0])
	sd.Url = resp.Request.Response.Header["Location"][0]
	sd.InitCookie = sd.purifyCookie(resp.Request.Response.Header["Set-Cookie"][0])
	sd.updateCSRFToken(resp.Body)
	return resp.StatusCode, err
}

func (sd *SamlClient) IdpLogin(User, Password, seed string) (int, error) {
	bodyString := fmt.Sprintf(
		"csrfmiddlewaretoken=%v&username=%v&password=%v&next=%%2F", sd.CsfrToken, User, Password,
	)
	idpLoginBody := strings.NewReader(bodyString)
	req, _ := http.NewRequest("Post", sd.Url, idpLoginBody)
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	req.Header.Set("Cookie", sd.Cookie)
	resp, err := sd.HttpClient.Do(req)
	if err != nil || resp.StatusCode != 200 {
		resp.Body.Close()
		return resp.StatusCode, err
	}
	if len(seed) > 0 {
		sd.updateCSRFToken(resp.Body)
		resp.Body.Close()
		token := otp.GetOtp(seed)
		bodyString = fmt.Sprintf(
			"csrfmiddlewaretoken=%v&username=%v&token_code=%v&next=%%2F",
			sd.CsfrToken, User, token,
		)
		req.Body = ioutil.NopCloser(strings.NewReader(bodyString))
		resp, err = sd.HttpClient.Do(req)
	}
	defer resp.Body.Close()
	buf := bufio.NewReaderSize(resp.Body, 65536)
	parser := xmlparser.NewXMLParser(buf, "form", "input").ParseAttributesOnly("form", "input")
	sd.SamlAssertion = url.Values{}
	for xml := range parser.Stream() {
		if xml.Name == "form" {
			sd.AcsMethod = xml.Attrs["method"]
			sd.AcsUrl = xml.Attrs["action"]
			continue
		}

		if xml.Name == "input" {
			name, ok := xml.Attrs["name"]
			if ok {
				sd.SamlAssertion.Add(name, xml.Attrs["value"])
			}
		}
	}
	return resp.StatusCode, err
}

func noRedirectfunc(req *http.Request, via []*http.Request) error {
	return errors.New("redirect disabled")
}

func (sd *SamlClient) DisableRedirect() {
	sd.HttpClient.CheckRedirect = noRedirectfunc
}

func (sd *SamlClient) EnableRedirect() {
	sd.HttpClient.CheckRedirect = nil
}
func handleRedirectCookie(req *http.Request, via []*http.Request) error {
	if len(via) > 0 {
		for _, cookie := range req.Response.Header["Set-Cookie"] {
			req.Header.Add("Cookie", cookie)
		}
	}

	return nil
}

func (sd *SamlClient) EnableRedirectCookie() {
	sd.HttpClient.CheckRedirect = handleRedirectCookie
	sd.HandleCookie = true
}

func (sd *SamlClient) DisableRedirectCookie() {
	sd.HttpClient.CheckRedirect = nil
	sd.HandleCookie = false
}

func (sd *SamlClient) GotoSpPage(expect string) (int, error) {
	sd.EnableRedirectCookie()
	body := strings.NewReader(sd.SamlAssertion.Encode())
	req, _ := http.NewRequest(strings.ToUpper(sd.AcsMethod), sd.AcsUrl, body)
	req.Header.Set("Cookie", sd.InitCookie)
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	resp, err := sd.HttpClient.Do(req)
	if err != nil || resp.StatusCode > 399 {
		return 400, errors.New("error when go to sp content, url is null")
	}
	defer resp.Body.Close()
	urlData := resp.Request.URL
	sd.Url = fmt.Sprintf("%s://%s%slogout", urlData.Scheme, urlData.Host, urlData.Path)
	Cookie := resp.Header["Set-Cookie"]
	for _, header := range Cookie {
		if strings.Contains(header, "token=") {
			sd.LogoutToken = header
		}
	}
	if len(expect) > 0 {
		d, _ := io.ReadAll(resp.Body)
		target := string(d)
		if !strings.Contains(target, expect) {
			err = fmt.Errorf("login failed! %s", target)
		}
	}
	return resp.StatusCode, err
}

func (sd *SamlClient) Logoff() (int, error) {
	sd.DisableRedirectCookie()
	sd.DisableRedirect()
	req, _ := http.NewRequest("GET", sd.Url, http.NoBody)
	req.Header.Add("Cookie", sd.LogoutToken)
	req.Header.Add("Content-Type", "application/x-www-form-urlencoded")
	resp, err := sd.HttpClient.Do(req)
	if resp.StatusCode == 302 {
		sd.Url = resp.Header["Location"][0]
		req, _ = http.NewRequest("GET", sd.Url, http.NoBody)
		req.Header.Add(
			"Cookie", fmt.Sprintf("csrftoken=%s;%s", sd.CsfrToken, sd.LogoutToken),
		)
		resp, err = sd.HttpClient.Do(req)
	}
	defer resp.Body.Close()
	return resp.StatusCode, err
}
