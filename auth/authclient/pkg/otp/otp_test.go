package otp

import (
	"testing"
)

func TestGetOtp(t *testing.T) {
	code := GetOtp("33574D384949414256415851534E59444C4E4847")
	t.Logf("Code: %v\n", code)
}
