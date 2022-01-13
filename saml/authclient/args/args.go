package args

import (
	"os"
	"strconv"
)

func getEnv(key string, defaultValue string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return defaultValue
}

// Generic
var URL = os.Getenv("URL")
var CONCURRENT, _ = strconv.Atoi(getEnv("CONCURRENT", "1"))
var REPEAT, _ = strconv.ParseInt(getEnv("REPEAT", "1"), 10, 64)
var PASSWORD = getEnv("PASSWORD", "fortinet")
var USER_PREFIX = getEnv("USER_PREFIX", "idptest")
var DISABLE_SSL_VERIFY = getEnv("DISABLE_SSL_VERIFY", "yes") == "yes"
var AUTHMODE = getEnv("AUTHMODE", "SAML")

// FAC Auth required
var FAC_ADMIN_USER = getEnv("FAC_ADMIN_USER", "admin")
var FAC_ADMIN_TOKEN = getEnv("FAC_ADMIN_TOKEN", "")
var FAC_USER_IDX_SLICE, _ = strconv.Atoi(getEnv("FAC_USER_IDX_SLICE", "500"))

// SAML Auth optional
var LOGOUT = getEnv("LOGOUT", "yes") == "yes"
