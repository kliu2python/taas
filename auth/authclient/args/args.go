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
var URL = getEnv("URL", "")
var PUSH_DATA = getEnv("PUSH_DATA", "yes") == "yes"
var LOG_LEVEL = getEnv("LOG_LEVEL", "info")
var CONCURRENT, _ = strconv.Atoi(getEnv("CONCURRENT", "1"))
var REPORT_INTERVAL, _ = strconv.Atoi(getEnv("REPORT_INTERVAL", "10"))
var REPEAT, _ = strconv.ParseInt(getEnv("REPEAT", "1"), 10, 64)
var PASSWORD = getEnv("PASSWORD", "fortinet")
var USER_PREFIX = getEnv("USER_PREFIX", "perftest")
var DISABLE_SSL_VERIFY = getEnv("DISABLE_SSL_VERIFY", "yes") == "yes"
var AUTHMODE = getEnv("AUTHMODE", "SAML")
var CLOSE_CONNECTION = getEnv("CLOSE_CONNECTION", "yes") == "yes"
var AUTH_SERVER_IP = getEnv("AUTH_SERVER_IP", "")
var TAAS_IP = getEnv("TAAS_IP", "localhost:8000")
var USE_TAAS = getEnv("USE_TAAS", "yes") == "yes"
var RESOURCE_POOL_NAME = getEnv("RESOURCE_POOL_NAME", "")
var RESOURCE_POOL_SIZE, _ = strconv.Atoi(getEnv("REQUEST_POOL_SIZE", "1"))

//RABBITMQ

var AMQP_URL = getEnv("AMQP_URL", "amqp://taas:taas@10.160.83.213:5672/faccloud")
var AMQP_QUEUE = getEnv("AMQP_QUEUE", "pushproxy_queue")

// MFA config
var MFA_RANDOM_TOKEN_HOLD_MAX, _ = strconv.Atoi(getEnv("MFA_RANDOM_TOKEN_HOLD_MAX", "0"))
var MFA_RANDOM_TOKEN_HOLD_MIN, _ = strconv.Atoi(getEnv("MFA_RANDOM_TOKEN_HOLD_MIN", "0"))

// FAC Auth required
var FAC_ADMIN_USER = getEnv("FAC_ADMIN_USER", "admin")
var FAC_ADMIN_TOKEN = getEnv("FAC_ADMIN_TOKEN", "")
var FAC_USER_IDX_SLICE, _ = strconv.Atoi(getEnv("FAC_USER_IDX_SLICE", "500"))

// OAuth required
var OAUTH_CLIENT_ID = getEnv("OAUTH_CLIENT_ID", "")
var OAUTH_CLIENT_SECRET = getEnv("OAUTH_CLIENT_SECRET", "")
var OAUTH_GRANT_TYPE = getEnv("OAUTH_GRANT_TYPE", "password")

// SAML Auth optional
var LOGOUT = getEnv("LOGOUT", "yes") == "yes"

// PushGateway
var PUSHGATEWAYURL = getEnv("PUSHGATEWAY_URL", "http://10.160.83.213:9091")
var PUSHGATEWAYJOB = getEnv("PUSHGATEWAY_JOB", "perf_job")
