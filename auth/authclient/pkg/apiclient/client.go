package apiclient

import (
	"errors"
	"fmt"
	"io"
	"net/http"
	"strings"

	"github.com/goccy/go-json"
)

type ApiClient struct {
	HttpClient      *http.Client
	CloseConnection bool
}

func (ac *ApiClient) Call(method string, url string, header *http.Header, body *strings.Reader, expectCode int, response interface{}) error {
	if body == nil {
		body = strings.NewReader("")
	}
	req, err := http.NewRequest(method, url, body)
	if err != nil {
		return err
	}

	if header != nil {
		req.Header = *header
	}
	req.Close = ac.CloseConnection
	resp, err := ac.HttpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	d, _ := io.ReadAll(resp.Body)
	if resp.StatusCode == expectCode {
		if response != nil {
			json.Unmarshal(d, response)
		}
		return nil
	}
	return errors.New(
		fmt.Sprintf(
			"Error for Api Call %s, status code: %d, response:%s",
			url, resp.StatusCode, d,
		),
	)
}
