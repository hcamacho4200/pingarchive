package main

import (
	"net"
	"time"
)

type PingData struct {
	id         int
	target     net.IP
	source     net.Addr
	sequence   int
	sentAt     time.Time
	receivedAt time.Time
	rtt        time.Duration
	err        error
}

func (p *PingData) UpdateReceivedAt(recv time.Time) error {
	p.receivedAt = recv
	p.rtt = p.receivedAt.Sub(p.sentAt)
	return nil
}


