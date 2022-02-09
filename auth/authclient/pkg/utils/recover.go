package utils

import "log"

func CatchError() {
	if err := recover(); err != nil {
		log.Println("Error when execution:", err)
	}
}
