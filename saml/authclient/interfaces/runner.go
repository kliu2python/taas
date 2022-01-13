package interfaces

type Runner interface {
	Run(idx int, c chan interface{})
}
