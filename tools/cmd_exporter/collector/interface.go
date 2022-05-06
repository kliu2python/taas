package collector

type Collector interface {
	InitMetrics()
	GetMetrics()
}
