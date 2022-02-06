package interfaces

import "automation/authclient/pkg/taas"

type Runner interface {
	Setup(idx int, rm *taas.ResourceManager)
	Run() bool
}
