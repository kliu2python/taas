package interfaces

type Runner interface {
	Setup(idx int)
	Run() bool
}
