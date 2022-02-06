package otp

import (
	"automation/authclient/args"
	"crypto/sha1"
	"encoding/base32"
	"encoding/hex"
	"fmt"
	"time"

	"github.com/xlzd/gotp"
)

var hasher = &gotp.Hasher{
	HashName: "sha1",
	Digest:   sha1.New,
}

var interval = 30
var digits = 6

func GetOtp(seed string) string {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("Error when get OTP code")
		}
	}()
	secret, _ := hex.DecodeString(seed)
	seed = base32.StdEncoding.EncodeToString(secret)
	if args.MFA_RANDOM_TOKEN_HOLD_MAX > 0 {
		time.Sleep(
			time.Duration(
				args.MFA_RANDOM_TOKEN_HOLD_MAX+args.MFA_RANDOM_TOKEN_HOLD_MIN,
			) * time.Second,
		)
	}
	totp := gotp.NewTOTP(seed, digits, int(interval), hasher)
	code := totp.Now()
	return code
}
