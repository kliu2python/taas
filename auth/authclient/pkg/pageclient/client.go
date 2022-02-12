package pageclient

import (
	"errors"
	"log"
	"net/http"
	"net/http/cookiejar"
	"strings"
)

type PageClient struct {
	HttpClient   *http.Client
	HandleCookie bool
}

// func printBody(body io.ReadCloser) {
// 	b, _ := io.ReadAll(body)
// 	fmt.Printf("%s", b)
// }

func (sd *PageClient) GetHttpClient() {
	jar, err := cookiejar.New(nil)
	if err != nil {
		log.Fatal(err)
	}
	sd.HttpClient = &http.Client{Jar: jar}
}

func (sd *PageClient) PurifyCookie(cookie string) string {
	return strings.Split(cookie, ";")[0]
}

func noRedirectfunc(req *http.Request, via []*http.Request) error {
	return errors.New("redirect disabled")
}

func (sd *PageClient) DisableRedirect() {
	sd.HttpClient.CheckRedirect = noRedirectfunc
}

func (sd *PageClient) EnableRedirect() {
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

func (sd *PageClient) EnableRedirectCookie() {
	sd.HttpClient.CheckRedirect = handleRedirectCookie
	sd.HandleCookie = true
}

func (sd *PageClient) DisableRedirectCookie() {
	sd.HttpClient.CheckRedirect = nil
	sd.HandleCookie = false
}
