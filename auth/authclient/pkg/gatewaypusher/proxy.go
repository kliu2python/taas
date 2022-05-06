package gatewaypusher

import (
	"automation/authclient/args"
	"encoding/json"
	"fmt"
	"log"

	"github.com/streadway/amqp"
)

func failOnError(err error, msg string) {
	if err != nil {
		log.Fatalf("%s: %s", msg, err)
	}
}

type GateWayRabbit struct {
	conn    *amqp.Connection
	chanel  *amqp.Channel
	labels  []map[string]string
	data    map[string][]float64
	threads int
	err     error
}

type PusherData struct {
	/*
		{
			category: bp_benchmark_cpu
			labels: [{
				label_name1: label1,
				label_name2: label2
			}]
			value: [xxx]
			description: "bp benchmark cpu"
			time: unix_time, time.time() // float
		}
	*/
	Catetory    string              `json:"category"`
	Labels      []map[string]string `json:"labels"`
	Values      []float64           `json:"values"`
	Description string              `json:"description"`
}

type PusherJson struct {
	Job  string        `json:"job"`
	Time int64         `json:"time"`
	Data []*PusherData `json:"data"`
}

func (gr *GateWayRabbit) PrepareData(threads int) {
	gr.labels = make([]map[string]string, threads)
	gr.data = make(map[string][]float64)
	gr.threads = threads

	for i := 0; i < threads; i++ {
		gr.labels[i] = map[string]string{"thread": fmt.Sprintf("thread-%d", i)}
	}

}

func (gr *GateWayRabbit) Connect() {
	gr.conn, gr.err = amqp.Dial(args.AMQP_URL)
	failOnError(gr.err, "Failed to connect to RabbitMQ")

	gr.chanel, gr.err = gr.conn.Channel()
	failOnError(gr.err, "Failed to open a channel")

	_, gr.err = gr.chanel.QueueDeclare(
		args.AMQP_QUEUE, // name
		false,           // durable
		false,           // delete when unused
		false,           // exclusive
		false,           // no-wait
		nil,             // arguments
	)
	failOnError(gr.err, "Failed to declare a queue")
}

func (gr *GateWayRabbit) pushToRabbit(body *PusherJson) {
	bodyJson, err := json.Marshal(body)
	if err != nil {
		log.Println(err.Error())
	}

	msg := amqp.Publishing{
		ContentType:  "application/octet-stream",
		DeliveryMode: amqp.Persistent,
		Priority:     0,
		Body:         bodyJson,
	}

	if err := gr.chanel.Publish("", args.AMQP_QUEUE, false, false, msg); err != nil {
		log.Println(err.Error())
	}
}

func (gr *GateWayRabbit) getData(data []int64) *PusherJson {
	var idx = data[0]
	v, ok := gr.data["result_pass_count"]
	if ok {
		v[idx] = float64(data[5])
	} else {
		new_result := make([]float64, gr.threads)
		new_result[idx] = float64(data[5])
		gr.data["result_pass_count"] = new_result
	}

	v, ok = gr.data["result_fail_count"]
	if ok {
		v[idx] = float64(data[6])
	} else {
		new_result := make([]float64, gr.threads)
		new_result[idx] = float64(data[6])
		gr.data["result_fail_count"] = new_result
	}

	v, ok = gr.data["result_api_time"]
	if ok {
		v[idx] = float64(data[3])
	} else {
		new_result := make([]float64, gr.threads)
		new_result[idx] = float64(data[3])
		gr.data["result_api_time"] = new_result
	}

	return &PusherJson{
		Job:  "auth_perf",
		Time: data[1],
		Data: []*PusherData{
			{

				Catetory:    "result_pass_count",
				Labels:      gr.labels,
				Values:      gr.data["result_pass_count"],
				Description: "total pass result",
			},
			{
				Catetory:    "result_fail_count",
				Labels:      gr.labels,
				Values:      gr.data["result_fail_count"],
				Description: "total fail result",
			},
			{
				Catetory:    "result_api_time",
				Labels:      gr.labels,
				Values:      gr.data["result_api_time"],
				Description: "api time",
			},
		},
	}
}

func (gr *GateWayRabbit) Push(data []int64) {
	/*
		c <- []int64{
			int64(idx),
			t2.Unix(),
			int64(total.Seconds()),
			int64(total.Milliseconds() / (complete - lastComplete)),
			complete,
			pass,
			fail,
		}
	*/
	dataToPush := gr.getData(data)
	gr.pushToRabbit(dataToPush)
}
