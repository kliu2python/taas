package args

import (
	"os"
	"strconv"
)

var URL = os.Getenv("URL")
var CONCURRENT, _ = strconv.Atoi(getEnv("CONCURRENT", "1"))
var REPEAT, _ = strconv.ParseInt(getEnv("REPEAT", "1"), 10, 64)
var PASSWORD = getEnv("PASSWORD", "fortinet")
var USER_PREFIX = getEnv("USER_PREFIX", "idptest")
var LOGOUT = getEnv("LOGOUT", "yes") == "yes"
var DISABLE_SSL_VERIFY = getEnv("DISABLE_SSL_VERIFY", "yes") == "yes"
var AUTHMODE = getEnv("AUTHMODE", "SAML")

func getEnv(key string, defaultValue string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return defaultValue
}
