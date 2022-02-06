package taas_test

import (
	"automation/authclient/pkg/taas"
	"fmt"
	"testing"
)

func TestResource(t *testing.T) {
	rm := taas.ResourceManager{}
	rm.Init("localhost:8000")
	rm.Request(3, "faccloud")
	res := rm.List()
	for _, r := range res {
		fmt.Printf("t: %v\n", r)
	}
	for i := 0; i < 10; i++ {
		r, _ := rm.Get()
		fmt.Printf("t: %v\n", r.CustomData.FacAdminToken)
	}
	rm.Release()
}
